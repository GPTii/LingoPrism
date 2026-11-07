#!/bin/bash
# Copy the server's nightly backups (database, uploaded photos, .env) to this PC, so losing the VM does not lose
# the backups too. Only files not already here are downloaded; copies older than KEEP_DAYS are removed here.
# Run by hand (scripts/pull-backups.bat) or by the Windows scheduled task "LingoPrism backup copy" every 10 days.
# The server keeps 14 days of backups, so copying every 10 days never misses one.
# env-* files hold the server's secrets: keep this folder private, never in git or a shared drive.
set -euo pipefail

# the server's address and SSH key live outside git, in private/secrets/server.env (see private.example/)
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/private/secrets/server.env"
# shellcheck source=/dev/null
[ -f "$ENV_FILE" ] && . "$ENV_FILE"
SERVER="${LINGOPRISM_SERVER:?Chua co private/secrets/server.env - xem private.example/README.md}"
KEY="${LINGOPRISM_KEY:-$HOME/.ssh/lingoprism.pem}"
DEST="${LINGOPRISM_BACKUP_DEST:-/d/backup-lingoprism}"
KEEP_DAYS="${KEEP_DAYS:-60}"
SSH=(ssh -i "$KEY" -o ConnectTimeout=20 -o BatchMode=yes "$SERVER")

mkdir -p "$DEST"
exec > >(tee -a "$DEST/pull.log") 2>&1
echo "== $(date '+%Y-%m-%d %H:%M') copying backups from $SERVER"

remote=$("${SSH[@]}" "cd backups && ls -1 db-*.dump media-*.tar.gz env-* 2>/dev/null")
new=0
for f in $remote; do
  [ -s "$DEST/$f" ] && continue
  scp -q -i "$KEY" -o BatchMode=yes "$SERVER:backups/$f" "$DEST/$f.part" && mv "$DEST/$f.part" "$DEST/$f"
  echo "   + $f ($(du -h "$DEST/$f" | cut -f1))"
  new=$((new + 1))
done
chmod 600 "$DEST"/env-* 2>/dev/null || true

old=$(find "$DEST" -maxdepth 1 \( -name 'db-*' -o -name 'media-*' -o -name 'env-*' \) -mtime +"$KEEP_DAYS" -print -delete | wc -l)
latest=$(ls -1t "$DEST"/db-*.dump 2>/dev/null | head -n 1)
echo "   $new new file(s), $old older than $KEEP_DAYS days removed; newest database backup: $(basename "${latest:-none}")"
echo "   folder: $(du -sh "$DEST" | cut -f1) in $DEST"
