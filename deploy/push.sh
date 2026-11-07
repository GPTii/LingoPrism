#!/bin/bash
# Push the code on this machine to the VPS and restart it (double-click scripts/deploy.bat).
# Sends the working tree as it is (committed or not) except secrets; big files (models, language sources) are only
# sent when they changed. Files deleted here are deleted on the server too. Data (database, photos, .env) stays.
set -euo pipefail
cd "$(dirname "$0")/.."

# the server's address and SSH key live outside git, in private/secrets/server.env (see private.example/)
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/private/secrets/server.env"
# shellcheck source=/dev/null
[ -f "$ENV_FILE" ] && . "$ENV_FILE"
SERVER="${LINGOPRISM_SERVER:?Chua co private/secrets/server.env - xem private.example/README.md}"
KEY="${LINGOPRISM_KEY:-$HOME/.ssh/lingoprism.pem}"
REMOTE=lingoprism
SSH=(ssh -i "$KEY" -o ConnectTimeout=20 "$SERVER")
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

[ -f "$KEY" ] || { echo "Khong tim thay SSH key: $KEY"; exit 1; }

echo "== 1/4 Liet ke file"
cp AI/runs/oiv7-pretrained/model_card.json BE/models/oiv7_model_card.json 2>/dev/null || true
{
  git ls-files -co --exclude-standard | grep -vE '^(MOBILE|AI|docs|private|private\.example)/'
  find BE/seed/sources -type f 2>/dev/null
  ls BE/models/yolov8l-oiv7-lingoprism-int8.onnx BE/models/oiv7l_model_card.json \
    BE/models/yolov8m-oiv7-lingoprism-int8.onnx BE/models/yolov10m-int8.onnx BE/models/clip-mobileclip2-s2.onnx \
    BE/models/yolov10n.onnx BE/models/embedder.onnx BE/models/oiv7_model_card.json \
    BE/models/phoneme-xlsr53-int8.onnx BE/models/phoneme-vocab.json
} | while IFS= read -r f; do [ -f "$f" ] && printf '%s\n' "$f"; done | sort -u > "$TMP/manifest"

BIG='^(BE/models/|BE/seed/sources/)'
grep -vE "$BIG" "$TMP/manifest" > "$TMP/send"
grep -E "$BIG" "$TMP/manifest" | xargs -d '\n' md5sum > "$TMP/big.local"
"${SSH[@]}" "cd $REMOTE && md5sum $(grep -E "$BIG" "$TMP/manifest" | tr '\n' ' ') 2>/dev/null" > "$TMP/big.remote" || true
norm() { awk '{ f = $2; sub(/^\*/, "", f); print $1, f }' "$1" | sort; }   # Windows md5sum writes "*path"
norm "$TMP/big.local" > "$TMP/a"; norm "$TMP/big.remote" > "$TMP/b"
comm -23 "$TMP/a" "$TMP/b" | cut -d' ' -f2- >> "$TMP/send"
echo "   $(wc -l < "$TMP/send") file se gui (file lon thay doi: $(comm -23 "$TMP/a" "$TMP/b" | wc -l))"

echo "== 2/4 Nen va gui len server"
tar -czf "$TMP/code.tgz" -T "$TMP/send"
scp -q -i "$KEY" "$TMP/code.tgz" "$TMP/manifest" "$SERVER:/tmp/"

echo "== 3/4 Giai nen, xoa file da xoa o may"
"${SSH[@]}" bash -s <<EOF
set -e
cd $REMOTE
tar -xzf /tmp/code.tgz
# delete files that no longer exist locally (never data, secrets, certificates or models)
find BE FE deploy -type f \
  -not -path 'BE/media/*' -not -path 'BE/staticfiles/*' -not -path 'deploy/certs/*' -not -path 'BE/models/*' \
  | sort | comm -23 - <(sort /tmp/manifest) | while IFS= read -r f; do echo "   xoa \$f"; rm -f "\$f"; done
rm -f /tmp/code.tgz /tmp/manifest
EOF

echo "== 3b Cap nhat cau hinh email / Google trong .env tren server"
# Only these keys are copied from this machine's .env; the server's own values (database, secret key, hosts)
# are never touched. The values travel over SSH and are never printed.
SYNC_KEYS='EMAIL_BACKEND EMAIL_HOST EMAIL_PORT EMAIL_USE_TLS EMAIL_HOST_USER EMAIL_HOST_PASSWORD DEFAULT_FROM_EMAIL GOOGLE_CLIENT_IDS GOOGLE_WEB_CLIENT_ID GEMINI_API_KEY GEMINI_MODEL ANTHROPIC_API_KEY AI_TALK_MODEL SENTRY_DSN WEB_CONCURRENCY'
: > "$TMP/env.sync"; chmod 600 "$TMP/env.sync"
if [ -f .env ]; then
  for k in $SYNC_KEYS; do
    line=$(grep -E "^$k=" .env | tail -n 1 | tr -d '
' || true)
    [ -n "${line#*=}" ] && printf '%s
' "$line" >> "$TMP/env.sync"
  done
fi
# Firebase service-account key (push notifications): private/secrets/firebase-adminsdk.json (git-ignored). It goes to
# ~/lingoprism/secrets/firebase.json (outside BE/FE/deploy, so step 3 never deletes it), readable only by the
# container user (uid 1000), mounted read-only at /app/secrets.
FIREBASE_KEY=${LINGOPRISM_FIREBASE_KEY:-$(ls private/secrets/firebase-adminsdk*.json 2>/dev/null | head -n 1 || true)}
if [ -n "$FIREBASE_KEY" ] && [ -f "$FIREBASE_KEY" ]; then
  "${SSH[@]}" "umask 077 && mkdir -p $REMOTE/secrets && cat > $REMOTE/secrets/firebase.json && chmod 600 $REMOTE/secrets/firebase.json \
    && { [ \$(id -u) = 1000 ] || sudo chown 1000 $REMOTE/secrets $REMOTE/secrets/firebase.json; }" < "$FIREBASE_KEY"
  printf '%s\n' "FIREBASE_CREDENTIALS_FILE=/app/secrets/firebase.json" >> "$TMP/env.sync"
  echo "   da gui khoa Firebase (thong bao day)"
fi
if [ -s "$TMP/env.sync" ]; then
  scp -q -i "$KEY" "$TMP/env.sync" "$SERVER:/tmp/lingoprism.env.sync"
  "${SSH[@]}" bash -s <<'EOF'
set -e
umask 077
cd lingoprism
f=/tmp/lingoprism.env.sync
cp .env .env.bak
keys=$(cut -d= -f1 "$f" | paste -sd'|')
{ grep -vE "^($keys)=" .env.bak || true; cat "$f"; } > .env
chmod 600 .env .env.bak
rm -f "$f"
echo "   da cap nhat: $(cut -d= -f1 .env | grep -cE "^($keys)$") muc (ban cu luu o .env.bak)"
EOF
else
  echo "   (khong co cau hinh email / Google trong .env may nay - bo qua)"
fi

echo "== 4/4 Build va khoi dong lai (vai phut)"
"${SSH[@]}" "cd $REMOTE && sh deploy/deploy.sh" 2>&1 | grep -vE '^#[0-9]+ |^ *=> |Building|naming to|exporting|writing image|unpacking' || true

echo
echo "Kiem tra:"
# only the domain: nginx closes connections that do not come through Cloudflare, so http://<IP>/ never answers
for url in https://lingoprism.id.vn/ https://lingoprism.id.vn/api/v1/health/; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$url" || true)
  echo "   $url -> $code"
done
