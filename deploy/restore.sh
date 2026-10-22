#!/bin/sh
# Restore a backup made by deploy/backup.sh (e.g. on a new VPS, with the stack already up):
#   sh deploy/restore.sh ~/backups/db-20261018-0300.dump ~/backups/media-20261018-0300.tar.gz
# Put the matching env-* file back as .env first: same DJANGO_SECRET_KEY = nobody gets logged out.
set -eu
cd "$(dirname "$0")/.."
DB_DUMP="$1"
MEDIA_TAR="${2:-}"
COMPOSE="docker compose -f docker-compose.prod.yml"

$COMPOSE stop backend worker
$COMPOSE exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$DB_DUMP"
if [ -n "$MEDIA_TAR" ]; then
  $COMPOSE run --rm -T --entrypoint "" backend tar -xzf - -C /app < "$MEDIA_TAR"
fi
$COMPOSE up -d
echo "restored $DB_DUMP"
