# OSCALIS

OSCALIS est une application web légère construite avec Flask qui permet de contrôler le DAW Reaper via OSC (Open Sound Control) et de gérer l'accès utilisateur via une base de données SQLite.

## Fonctionnalités

* Interface web pour contrôler des paramètres dans Reaper (lecture, pause, position, etc.)
* Authentification sécurisée des utilisateurs (hashing des mots de passe avec Werkzeug)
* Gestion des comptes utilisateurs via SQLite (`users.db`)
* Communication OSC avec Reaper grâce à `python-osc`

## Prérequis

* Python 3.7 ou supérieur
* pip
* (Optionnel) virtualenv / venv
* **Reaper** installé

## Installation

1. **Cloner le dépôt**

   ```bash
   git clone https://github.com/Utilisateur/TouchBeat2.git
   cd TouchBeat2
   ```

2. **Créer un environnement virtuel (fortement recommandé)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate    # Windows
   ```

3. **Installer les dépendances**

   ```bash
   pip install -r requirements.txt
   ```

   Si vous n'avez pas de `requirements.txt`, générez-le avec :

   ```bash
   pip freeze > requirements.txt
   ```

## Configuration

* **Clé secrète Flask**
  Définissez la variable d'environnement `FLASK_SECRET_KEY` pour sécuriser les sessions :

  ```bash
  export FLASK_SECRET_KEY="une_chaine_secrete_complexe"
  ```

  Sous Windows (PowerShell) :

  ```powershell
  setx FLASK_SECRET_KEY "une_chaine_secrete_complexe"
  ```

* **Mode production**
  Assurez-vous de ne **pas** exécuter l'application en mode debug en production :

  ```bash
  export FLASK_ENV=production
  ```

  Utilisez un serveur WSGI dédié (gunicorn, uWSGI, etc.) plutôt que `flask run`.

## Intégration du script Lua

Pour que TouchBeat2 récupère les données de Reaper en temps réel, un script Lua s’exécute côté Reaper :

1. **Emplacement**
   Copiez `test.lua` (ou renommez-le `touchbeat.lua`) dans le dossier **Scripts** de votre installation Reaper :

   * Sous Windows : `%APPDATA%\REAPER\Scripts\`
   * Sous macOS : `~/Library/Application Support/REAPER/Scripts/`
   * Sous Linux : `~/.config/REAPER/Scripts/`

2. **Dépendance JSON**
   Placez `dkjson.lua` dans le même répertoire. Le script charge cette bibliothèque pour encoder/décoder les données JSON.

3. **Exécution**

   * Dans Reaper, ouvrez **Actions > Show Action List > Load** et sélectionnez `test.lua`.
   * Cliquez sur **Run**. Le script tourne en boucle grâce à `reaper.defer` et écrit périodiquement trois fichiers JSON dans le dossier ressource Reaper :

     * `tracks.json`
     * `instrument_changes.json`
     * `input_changes.json`

4. **Communication avec le serveur**
   Le serveur Flask (`server.py`) lit/écrit ces mêmes fichiers JSON dans `%APPDATA%\REAPER\` et envoie/reçoit des messages OSC pour piloter Reaper.

   * Démarrez le serveur (cf. section “Lancer l’application”) **avant** d’exécuter le script Lua.

## Structure du projet

```
TouchBeat2/
│
├── server.py          # Serveur Flask principal
├── users.db           # Base de données SQLite des utilisateurs (à ne pas versionner)
├── requirements.txt   # Dépendances pip (versions figées conseillées)
├── LICENSE            # Licence MIT
│
└── templates/         # Templates HTML
    ├── index.html     # Interface principale de contrôle Reaper
    └── login.html     # Page de connexion sécurisée
```

## Lancer l'application

```bash
# Activez votre environnement
export FLASK_APP=server.py
flask run
```

Accédez ensuite à `http://localhost:5000` dans votre navigateur.

## Dépendances

* Flask
* python-osc
* Werkzeug


