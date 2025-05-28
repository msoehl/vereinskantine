#!/bin/bash

# Konfiguration
REPO_URL="https://github.com/msoehl/vereinskantine.git"
TARGET_DIR="/home/kantine/Documents/vereinskantine"
BRANCH="dev"
START_SCRIPT="start.sh"
PACKAGE_PATH="dist/raspberry-package.tar.gz"

echo "🔄 Starte Git-Update-Prozess aus Branch '$BRANCH'..."

# Backup .env und kantine.db (wenn vorhanden)
echo "💾 Sichere .env und kantine.db..."
ENV_BACKUP="/tmp/vereinskantine_env_backup"
DB_BACKUP="/tmp/vereinskantine_db_backup"

[ -f "$TARGET_DIR/env" ] && cp "$TARGET_DIR/env" "$ENV_BACKUP"
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

# Wiederherstellen von Backups
echo "♻️ Stelle .env und kantine.db wieder her..."
[ -f "$ENV_BACKUP" ] && cp "$ENV_BACKUP" "$TARGET_DIR/env"
[ -f "$DB_BACKUP" ] && cp "$DB_BACKUP" "$TARGET_DIR/kantine.db"

# Startskript ausführen
chmod +x "$START_SCRIPT"
echo "🚀 Starte Anwendung..."
./"$START_SCRIPT"

echo "✅ Update abgeschlossen."
