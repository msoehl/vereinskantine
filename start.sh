#!/bin/bash

cd "$(dirname "$0")"

# Umgebung initialisieren
if [ ! -d ".venv" ]; then
  echo "📦 Erstelle virtuelle Umgebung..."
  python3 -m venv .venv
fi

source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt


# Aufräumen: lösche alle überflüssigen Projektdateien
echo "🧹 Entferne nicht benötigte Ordner und Dateien..."

for item in "Frontend" "Backend" "kantine-web" "dist" "__pycache__" ".git" ".github" "raspberry-package.tar.gz" ".env_sample" "README.md" ".gitignore"; do
  if [ -e "$item" ]; then
    echo "🗑️ Lösche: $item"
    rm -rf "$item"
  fi
done

echo "✅ Bereinigung abgeschlossen. System bereit für den Produktivbetrieb."


# Backend starten
echo "🚀 Starte Backend..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend > backend.log 2>&1 &

# Warten, bis Backend erreichbar ist
echo "⏳ Warte auf Backend..."
for i in {1..30}; do
  if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Backend ist bereit."
    break
  fi
  sleep 1
done

if ! curl -s http://localhost:8000/products > /dev/null; then
  echo "❌ Backend nicht erreichbar. Abbruch."
  kill $BACKEND_PID
  exit 1
fi

# GUI starten, falls möglich
if [ -n "$DISPLAY" ]; then
  echo "🖥️ Starte GUI..."
  python3 gui/KantinenUI.py
else
  echo "⚠️ Keine grafische Oberfläche erkannt (DISPLAY nicht gesetzt) – GUI wird nicht gestartet."
fi
