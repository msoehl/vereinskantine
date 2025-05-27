# VereinsKantine

Ein digitales System zur Verwaltung der Vereinsverpflegung – bestehend aus einem Backend (Python/FastAPI), einer lokalen GUI (`KantinenUI.py`) sowie einer Weboberfläche.

## 📦 Was ist enthalten?

- **Backend (FastAPI)** – verarbeitet Daten, bietet REST-API
- **Web-Frontend** – für Admins über den Browser erreichbar
- **Lokale GUI** – einfache Bedienoberfläche z. B. für Verkauf vor Ort
- **Vereinsflieger-Integration** – Anbindung an externe Mitglieder-API

---

## ⚙️ Voraussetzungen

Das System läuft auf jedem Raspberry Pi oder Linux-System mit:

- 🐍 Python 3.11 oder höher
- 📦 Git

---

## 🧾 Installation

```bash
# 1. Repository klonen
git clone https://github.com/msoehl/vereinskantine.git
cd vereinskantine

# 2. Build-Paket entpacken
tar -xzf dist/raspberry-package.tar.gz
cd output

# 3. Umgebungsvariablen konfigurieren
cp .env_sample .env
# Bearbeite .env mit deinen Daten

# 4. Starten
chmod +x start.sh
./start.sh
```

---

## 🖥️ Bedienung

Nach dem Start über `start.sh`:

- 📡 **Backend und Web-Frontend** erreichbar unter:  
  `http://<raspberry-ip>:8000`

- 🖥️ **Lokale GUI** (KantinenUI) startet automatisch

---

## 🌐 Web-UI (Admin-Oberfläche)

Die Weboberfläche ist erreichbar unter:

```
http://<raspberry-ip>:8000
```

Dort können Administratoren:

- Produkte verwalten
- Kassenstände prüfen
- Benutzerrollen zuweisen
- Mitglieder importieren (z. B. von Vereinsflieger)

### 🔐 Standard-Login

| Benutzername | Passwort    | Rolle        |
|--------------|-------------|--------------|
| `admin`      | `admin`  | Administrator |

> 🔒 Bitte ändere das Standard-Passwort nach dem ersten Login!

---

## 🔗 Vereinsflieger API

Das Backend enthält eine Integration zur Vereinsflieger API, um:

- Mitglieder zu synchronisieren


### 🔐 Zugang

Die Zugangsdaten zur Vereinsflieger API werden über eine `.env`-Datei bereitgestellt.  
Nutze die bereitgestellte Vorlage `.env_sample`:

```env
VFL_USERNAME=dein_benutzername
VFL_PASSWORD=dein_passwort
VFL_APIKEY=dein_api_key
VFL_CID=dein_club_id
```

Diese Datei wird beim Start automatisch geladen (über `dotenv`).

---

## 🛠 Fehlerbehebung

Falls beim Start Probleme auftreten:

- Stelle sicher, dass `requirements.txt` vollständig installiert wurde
- Falls nötig: virtuelle Umgebung löschen und neu erstellen:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ℹ️ Weitere Hinweise

- Aktuelle Builds findest du im Ordner `dist/`
- Die Build-Pipeline erzeugt bei jedem Commit auf `dev` ein neues Paket
- Das Startskript `start.sh` kümmert sich um alles Weitere

---

## 📄 Lizenz

MIT – Nutzung & Anpassung erlaubt.
