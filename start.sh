#!/bin/bash

# Projektverzeichnis annehmen (optional)
cd "$(dirname "$0")"

# Python-Umgebung einrichten (falls noch nicht vorhanden)
if [ ! -d ".venv" ]; then
  echo "📦 Erstelle virtuelle Umgebung..."
  python3 -m venv .venv
fi

# Umgebung aktivieren
source .venv/bin/activate

# Dependencies installieren (nur beim ersten Start nötig)
pip install -r requirements.txt

# Backend starten (liefert auch Web-Frontend aus)
echo "🚀 Starte Backend (inkl. Web-Frontend)..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# GUI-Anwendung starten
echo "🖥️ Starte GUI..."
python3 gui/KantinenUI.py
