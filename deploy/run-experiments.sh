#!/usr/bin/env bash
# Run the thesis experiments on the production server and bring the results back for the report
# (double-click scripts/run-experiments.bat). Results: AI/report/experiments/production.json;
# AI/notebooks/09_geofence_realtime.ipynb and 10_production_report.ipynb draw the tables and charts from it.
#   run-experiments.sh          everything: SM-2/FSRS, GA (measured only, never applied), VIP, geofence, realtime,
#                               then the benchmark (Smart Distractor, Proximity, prediction, scheduling) – ~5 minutes
#   run-experiments.sh quick    geofence + realtime only (~15 s)
set -euo pipefail
cd "$(dirname "$0")/.."

# the server's address and SSH key live outside git, in private/secrets/server.env (see private.example/)
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/private/secrets/server.env"
# shellcheck source=/dev/null
[ -f "$ENV_FILE" ] && . "$ENV_FILE"
SERVER="${LINGOPRISM_SERVER:?Chua co private/secrets/server.env - xem private.example/README.md}"
KEY="${LINGOPRISM_KEY:-$HOME/.ssh/lingoprism.pem}"
OUT=AI/report/experiments/production.json
[ -f "$KEY" ] || { echo "Khong tim thay SSH key: $KEY"; exit 1; }
mkdir -p "$(dirname "$OUT")"

if [ "${1:-}" = "quick" ]; then
  STEPS="geofence realtime"; BENCH=0; echo "== Chay geofence + realtime tren server (khoang 15 giay)"
else
  STEPS="srs ga vip geofence realtime"; BENCH=1; echo "== Chay tat ca thuc nghiem tren server (khoang 5 phut, GA khong ap dung vao he thong)"
fi
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$SERVER" STEPS="'$STEPS'" BENCH=$BENCH bash -s > "$OUT.tmp" <<'REMOTE'
set -e
cd ~/lingoprism
COMPOSE="docker compose -f docker-compose.prod.yml"
# </dev/null: otherwise docker reads the rest of this script (our stdin) and the lines below never run
$COMPOSE exec -T backend python manage.py run_algorithm_experiments --no-apply --only $STEPS </dev/null >&2
if [ "$BENCH" = 1 ]; then
  $COMPOSE exec -T backend python manage.py benchmark_algorithms </dev/null >&2
fi
$COMPOSE exec -T backend python manage.py shell <<'PY'
import json
from django.conf import settings
from apps.accounts.models import User
from apps.algorithms.experiments import latest
from apps.learning.models import ReviewLog
demo = ("@lingoprism.local", "@example.com", "@bench.invalid")
logs = ReviewLog.objects.filter(first_try=True)
real = logs
for d in demo:
    real = real.exclude(user__email__endswith=d)
learners = User.objects.filter(role="learner")
for d in demo:
    learners = learners.exclude(email__endswith=d)
data = {"review_logs": logs.count(), "review_logs_real_users": real.count(),
        "real_learners": learners.count(), "real_learners_with_reviews": learners.filter(review_logs__isnull=False).distinct().count()}
runs = {k: v for k, v in latest().items() if k not in ("yolo", "word2vec")}
print(json.dumps({"where": "production", "hosts": settings.ALLOWED_HOSTS[:1], "data": data, "runs": runs},
                 default=str, ensure_ascii=False))
PY
REMOTE
# the shell may print a banner before the JSON: keep the JSON line only
grep '^{"where"' "$OUT.tmp" > "$OUT" || { echo "Khong nhan duoc ket qua tu server:"; cat "$OUT.tmp"; exit 1; }
rm -f "$OUT.tmp"
python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); print('   da luu', sys.argv[1], '-', ', '.join(d['runs']))" "$OUT"
