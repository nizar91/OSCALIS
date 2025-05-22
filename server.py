import json
import os
import sqlite3
import socket

from flask import Flask, request, render_template, redirect, url_for, session, g
from pythonosc.udp_client import SimpleUDPClient
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration Flask
app = Flask(__name__)
app.secret_key = "touchbeat_secret_key"  # Clé secrète pour sécuriser les sessions
DATABASE = "users.db"

REAPER_IP = socket.gethostbyname(socket.gethostname())
REAPER_PORT = 8000
osc_client = SimpleUDPClient(REAPER_IP, REAPER_PORT)

instrument_file = os.path.join(os.getenv("APPDATA"), "REAPER", "instrument_changes.json")
track_file_path = os.path.join(os.getenv("APPDATA"), "REAPER", "tracks.json")

# Connexion à la base de données
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Authentification
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor = get_db().cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result and check_password_hash(result[0], password):
            session["user"] = username
            return redirect("/")
        else:
            return "Identifiants incorrects", 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# Vérification connexion
def require_login():
    if "user" not in session:
        return redirect("/login")

# Application principale
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route("/set_volume", methods=["POST"])
def set_volume():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    data = request.json
    osc_client.send_message(f"/track/{data['track']}/volume", data['volume'])
    return {"message": "Volume changé"}

@app.route("/set_pan", methods=["POST"])
def set_pan():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    data = request.json
    osc_client.send_message(f"/track/{data['track']}/pan", data['pan'])
    return {"message": "Pan changé"}


@app.route("/toggle_record_arm", methods=["POST"])
def toggle_record_arm():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    data = request.json
    track_id = int(data["track"])
    record = bool(data["record"])
    value = 1 if record else 0
    osc_client.send_message(f"/track/{track_id}/recarm", value)
    return {"message": f"Piste {track_id} {'armé' if record else 'désarmé'} pour enregistrement"}

@app.route("/add_track", methods=["POST"])
def add_track():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    osc_client.send_message("/action", 40001)
    return {"message": "Piste ajoutée"}

@app.route("/delete_track", methods=["POST"])
def delete_track():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    data = request.json
    track = str(data["track"])

    for i in range(1, 33):
        osc_client.send_message(f"/track/{i}/select", 0)

    osc_client.send_message(f"/track/{track}/select", 1)
    osc_client.send_message("/action", 40005)

    if os.path.exists(instrument_file):
        with open(instrument_file, "r") as f:
            changes = json.load(f)

        if track in changes:
            del changes[track]
            with open(instrument_file, "w") as f:
                json.dump(changes, f)

    return {"message": f"Piste {track} supprimée."}

@app.route("/track_data", methods=["GET"])
def get_track_data():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403

    instruments = [
        "DSK Strings (x86) (DSK Music)",
        "Electric (AIR Music Technology)",
        "Hype (AIR Music Technology)",
        "MPC Beats (Akai Professional)",
        "Pianoteq 8 (Modartt)",
        "ReaSamplOmatic5000 (Cockos)",
        "ReaSynDr (Cockos)",
        "ReaSynth (Cockos)"
    ]

    current_instruments = {}
    if os.path.exists(instrument_file):
        with open(instrument_file, 'r') as f:
            current_instruments = json.load(f)

    tracks = []
    if os.path.exists(track_file_path):
        with open(track_file_path, 'r') as f:
            try:
                data = json.load(f)
                tracks = data.get("tracks", [])
            except Exception as e:
                print(f"Erreur lecture tracks.json : {e}")

    return {
        "tracks": tracks,
        "instruments": instruments,
        "current_instruments": current_instruments
    }

@app.route("/set_input", methods=["POST"])
def set_input():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    data = request.json
    track_id = str(data["track"])
    input_value = data["input"]

    input_map = {
        "mono1": 0,
        "mono2": 1,
        "stereo1_2": 512,
        "midi_all": 6112,
        "midi_virtual": 1025
    }

    input_final = input_map.get(input_value, 0)

    input_file = os.path.join(os.getenv("APPDATA"), "REAPER", "input_changes.json")

    if os.path.exists(input_file):
        with open(input_file, 'r') as f:
            changes = json.load(f)
    else:
        changes = {}

    changes[track_id] = input_final

    with open(input_file, 'w') as f:
        json.dump(changes, f)

    return {"message": f"Input de la piste {track_id} défini à {input_final}"}

@app.route("/set_instrument", methods=["POST"])
def set_instrument():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    data = request.json
    track = str(data["track"])
    instrument = data["instrument"]

    try:
        if os.path.exists(instrument_file):
            with open(instrument_file, 'r') as f:
                changes = json.load(f)
        else:
            changes = {}
        changes[track] = instrument
        with open(instrument_file, 'w') as f:
            json.dump(changes, f)
    except Exception as e:
        return {"error": str(e)}, 500

    return {"message": f"Instrument de la piste {track} défini à {instrument}"}

@app.route("/set_reverb", methods=["POST"])
def set_reverb():
    if "user" not in session:
        return {"error": "Unauthorized"}, 403
    data = request.get_json()
    track  = str(data["track"])
    active = bool(data["active"])
    wet    = float(data["wet"])
    dry    = float(data["dry"])

    # Stockage local pour que Lua lise
    reverb_file = os.path.join(os.getenv("APPDATA"), "REAPER", "reverb_changes.json")
    if os.path.exists(reverb_file):
        with open(reverb_file, "r") as f:
            changes = json.load(f)
    else:
        changes = {}
    changes[track] = {"active": active, "wet": wet, "dry": dry}
    with open(reverb_file, "w") as f:
        json.dump(changes, f)

    return {"message": f"Réverbération piste {track} mise à jour"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
