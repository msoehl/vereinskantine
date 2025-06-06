#!/bin/bash

# Konfiguration
REPO_URL="https://github.com/msoehl/vereinskantine.git"
TARGET_DIR="/home/kantine/Documents/vereinskantine"
BRANCH="dev"
START_SCRIPT="start.sh"
PACKAGE_PATH="dist/raspberry-package.tar.gz"

SCRIPT_NAME=$(basename "$0")
SCRIPT_TMP="/tmp/$SCRIPT_NAME"

if [[ "$0" != "$SCRIPT_TMP" ]]; then
  echo "📦 Kopiere mich selbst nach /tmp und starte dort neu..."
  cp "$0" "$SCRIPT_TMP"
  chmod +x "$SCRIPT_TMP"
  exec "$SCRIPT_TMP"
  exit 0
fi

echo "🔄 Starte Git-Update-Prozess aus Branch '$BRANCH'..."

# Backup .env und kantine.db (wenn vorhanden)
echo "💾 Sichere .env und kantine.db..."
ENV_BACKUP="/tmp/vereinskantine_env_backup"
DB_BACKUP="/tmp/vereinskantine_db_backup"

[ -f "$TARGET_DIR/Backend/.env" ] && cp "$TARGET_DIR/Backend/.env" "$ENV_BACKUP"
[ -f "$TARGET_DIR/kantine.db" ] && cp "$TARGET_DIR/kantine.db" "$DB_BACKUP"

# Vorheriges Verzeichnis löschen
echo "🧹 Entferne alte Version..."
cd ~
rm -rf "$TARGET_DIR"

# Repository neu klonen
echo "📥 Klone Repository von '$BRANCH'..."
git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR" || {
    echo "❌ Fehler beim Klonen von $REPO_URL"
    exit 1
}

cd "$TARGET_DIR" || {
    echo "❌ Zielverzeichnis konnte nicht betreten werden."
    exit 1
}

# Paket entpacken (falls vorhanden)
if [ -f "$PACKAGE_PATH" ]; then
    echo "📦 Entpacke $PACKAGE_PATH..."
    tar -xzf "$PACKAGE_PATH" || {
        echo "❌ Fehler beim Entpacken von $PACKAGE_PATH"
        exit 1
    }
else
    echo "⚠️ Kein Paket gefunden unter: $PACKAGE_PATH – überspringe Entpacken."
fi


echo "♻️ Stelle .env und kantine.db wieder her..."
[ -f "$ENV_BACKUP" ] && cp "$ENV_BACKUP" "$TARGET_DIR/Backend/.env"
[ -f "$DB_BACKUP" ] && cp "$DB_BACKUP" "$TARGET_DIR/kantine.db"


chmod +x "$START_SCRIPT"
sleep 5
echo "🚀 Starte Anwendung..."
./"$START_SCRIPT"

echo "✅ Update abgeschlossen."
