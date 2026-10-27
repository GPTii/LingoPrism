#!/bin/sh
# Proves the latest backup can be restored, without touching the live database:
#   sh deploy/restore-drill.sh [~/backups/db-YYYYMMDD-HHMM.dump]
# The dump goes into a scratch database next to the real one, every table's row count is compared with the live
# database (it may have moved on a little since the backup ran), and the scratch database is dropped.
set -eu
cd "$(dirname "$0")/.."
DUMP="${1:-$(ls -t "${BACKUP_DIR:-$HOME/backups}"/db-*.dump | head -n 1)}"
COMPOSE="${COMPOSE:-docker compose -f docker-compose.prod.yml}"
SCRATCH=restore_drill
psql_in() { $COMPOSE exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d $1 -At -F ' ' -c \"$2\""; }
COUNT_SQL="SELECT string_agg(format('SELECT %L, count(*) FROM %I', table_name, table_name), ' UNION ALL ' ORDER BY table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"

echo "backup: $DUMP ($(du -h "$DUMP" | cut -f1))"
psql_in postgres "DROP DATABASE IF EXISTS $SCRATCH" >/dev/null
psql_in postgres "CREATE DATABASE $SCRATCH" >/dev/null
start=$(date +%s)
$COMPOSE exec -T db sh -c "pg_restore -U \"\$POSTGRES_USER\" -d $SCRATCH --no-owner" < "$DUMP"
echo "restored in $(( $(date +%s) - start ))s"

counts() { psql_in "$1" "$(psql_in "$1" "$COUNT_SQL")" | sort; }
counts "\$POSTGRES_DB" > /tmp/drill.live
counts "$SCRATCH" > /tmp/drill.restored
echo "tables: $(wc -l < /tmp/drill.live) live, $(wc -l < /tmp/drill.restored) restored"
echo "rows:   $(awk '{s+=$2} END {print s}' /tmp/drill.live) live, $(awk '{s+=$2} END {print s}' /tmp/drill.restored) restored"
join /tmp/drill.live /tmp/drill.restored | awk '$2 != $3 {print "  differs (new rows since the backup?):", $1, $3, "->", $2}'
psql_in postgres "DROP DATABASE $SCRATCH" >/dev/null
rm -f /tmp/drill.live /tmp/drill.restored
echo "drill ok: scratch database dropped"
