import sqlite3
from werkzeug.security import generate_password_hash

# Connexion à la base de données
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Création de la table "users"
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Ajout d'un utilisateur "admin" avec mot de passe "admin123"
username = "admin"
password = "admin123"
hashed_password = generate_password_hash(password)

cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))

conn.commit()
conn.close()

print("Base de données users.db créée avec succès.")
