#!/bin/sh
# Back up the database and uploaded media into ~/backups (keeps the last 14 days).
#   sh deploy/backup.sh                 # by hand
#   crontab (the VM is on UTC: 20:00 = 03:00 in Vietnam): 0 20 * * * cd ~/lingoprism && sh deploy/backup.sh >> ~/backups/backup.log 2>&1
# Copy the files off the server regularly (scp), a backup on the same disk does not survive losing the VPS.
set -eu
cd "$(dirname "$0")/.."
DEST="${BACKUP_DIR:-$HOME/backups}"
STAMP=$(date +%Y%m%d-%H%M)
mkdir -p "$DEST"
COMPOSE="docker compose -f docker-compose.prod.yml"

$COMPOSE exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$DEST/db-$STAMP.dump"
$COMPOSE exec -T backend tar -czf - -C /app media > "$DEST/media-$STAMP.tar.gz"
cp .env "$DEST/env-$STAMP" && chmod 600 "$DEST/env-$STAMP"

find "$DEST" -name 'db-*' -mtime +14 -delete
find "$DEST" -name 'media-*' -mtime +14 -delete
find "$DEST" -name 'env-*' -mtime +14 -delete
echo "$(date) backup ok: $DEST/db-$STAMP.dump"
