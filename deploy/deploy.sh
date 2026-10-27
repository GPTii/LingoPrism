#!/bin/sh
# Build and (re)start LingoPrism on the VPS, from the project folder: sh deploy/deploy.sh
# First run also: creates .env with random secrets, a self-signed origin certificate (Cloudflare "Full"),
# seeds the database, gives the demo admin/staff accounts random passwords, schedules the daily backup.
set -eu
cd "$(dirname "$0")/.."
DOMAIN="${DOMAIN:-lingoprism.id.vn}"
COMPOSE="docker compose -f docker-compose.prod.yml"
rand() { openssl rand -hex "$1"; }

if [ ! -f .env ]; then
  IP=$(curl -fsS https://api.ipify.org || echo "")
  cat > .env <<EOF
POSTGRES_DB=lingoprism
POSTGRES_USER=lingoprism
POSTGRES_PASSWORD=$(rand 24)
DJANGO_SECRET_KEY=$(rand 40)
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN${IP:+,$IP}
CORS_ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
NUM_PROXIES=1
API_DOCS=0
GOOGLE_CLIENT_IDS=
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EOF
  chmod 600 .env
  echo "created .env"
fi

if [ ! -f deploy/certs/origin.crt ]; then
  mkdir -p deploy/certs
  openssl req -x509 -nodes -newkey rsa:2048 -days 3650 -subj "/CN=$DOMAIN" \
    -keyout deploy/certs/origin.key -out deploy/certs/origin.crt
  chmod 644 deploy/certs/origin.crt deploy/certs/origin.key
fi

$COMPOSE up -d --build
# the backend container migrates on start (entrypoint.sh): wait for it before touching the database
until $COMPOSE exec -T backend python manage.py migrate --check >/dev/null 2>&1; do sleep 3; done
# nginx looks up "backend" once, when it starts: a recreated backend has a new IP (502 for every API call) and an
# edited deploy/nginx/nginx.conf is mounted, not built in, so compose does not restart web for it. Reload both ways.
$COMPOSE exec -T web nginx -t && $COMPOSE exec -T web nginx -s reload
$COMPOSE exec -T backend python manage.py check --deploy --fail-level ERROR >/dev/null 2>&1 \
  || $COMPOSE exec -T backend python manage.py check --deploy --fail-level ERROR   # quiet unless it fails

if [ "$($COMPOSE exec -T backend python manage.py shell -c 'from apps.vocab.models import Word; print(Word.objects.exists())' | tail -n 1)" != "True" ]; then
  $COMPOSE exec -T backend python manage.py seed_all --offline
  $COMPOSE exec -T backend python manage.py shell -c "
import secrets
from apps.accounts.models import User
lines = []
for email in ['admin@lingoprism.local', 'staff@lingoprism.local']:
    u = User.objects.filter(email=email).first()
    if u:
        pw = secrets.token_urlsafe(12)
        u.set_password(pw); u.save()
        lines.append(f'{email}  {pw}')
print('\n'.join(lines))
" > ADMIN_PASSWORDS.txt
  chmod 600 ADMIN_PASSWORDS.txt
  echo "admin/staff passwords: $(pwd)/ADMIN_PASSWORDS.txt"
fi
# demo learners are seeded with the shared password printed in the public repo: each gets its own, kept with the
# admin ones (every deploy, so accounts seeded before this existed are fixed too)
$COMPOSE exec -T backend python manage.py secure_demo_accounts | tr -d '\r' >> ADMIN_PASSWORDS.txt
chmod 600 ADMIN_PASSWORDS.txt

# detector: Open Images model (232 labels) + COCO yolov10m ensemble, both INT8, + CLIP re-check, see AI/README.md
# (BE/models is not in git: copy the .onnx files and AI/runs/oiv7-pretrained/model_card.json there first)
if [ -f BE/models/yolov8m-oiv7-lingoprism-int8.onnx ] && [ -f BE/models/oiv7_model_card.json ]; then
  $COMPOSE exec -T backend python manage.py register_model \
    --onnx /app/models/yolov8m-oiv7-lingoprism-int8.onnx --card /app/models/oiv7_model_card.json
fi

# algorithms chosen by the benchmark on the dev machine (manage.py algorithm_config --export deploy/algorithm_config.json):
# loaded only when the file changed, so a choice made later on the admin page is not overwritten by every deploy
APPLIED="$HOME/.lingoprism_algorithm_config.md5"
if [ -f deploy/algorithm_config.json ] && ! md5sum -c --status "$APPLIED" 2>/dev/null; then
  $COMPOSE exec -T backend python manage.py algorithm_config --load - < deploy/algorithm_config.json \
    && md5sum deploy/algorithm_config.json > "$APPLIED"
fi


# the VM runs on UTC: 20:00 UTC = 03:00 in Vietnam, when nobody is learning
CRON="0 20 * * * cd $(pwd) && sh deploy/backup.sh >> \$HOME/backups/backup.log 2>&1"
mkdir -p "$HOME/backups"
( crontab -l 2>/dev/null | grep -v 'deploy/backup.sh' || true; echo "$CRON" ) | crontab -

docker image prune -f >/dev/null   # old builds would slowly fill the 29 GB disk
$COMPOSE ps
