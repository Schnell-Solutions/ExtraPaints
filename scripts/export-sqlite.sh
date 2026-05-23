#!/bin/sh
# Export db.sqlite3 to extrapaints-data.json (run on server before Postgres import).
set -e
cd "$(dirname "$0")/.."

if [ ! -f db.sqlite3 ]; then
  echo "Error: db.sqlite3 not found in $(pwd)"
  exit 1
fi

if [ ! -f .env ]; then
  echo "Error: .env not found"
  exit 1
fi

cp .env .env.production.bak
SECRET=$(grep ^SECRET_KEY= .env.production.bak | cut -d= -f2-)

# Minimal env so compose does not load DEBUG=0 during export
cat > .env << EOF
DEBUG=1
POSTGRES_PASSWORD=temp
ALLOWED_HOSTS=localhost
SECRET_KEY=$SECRET
EOF

chmod +x docker/entrypoint.sh 2>/dev/null || true

echo "Exporting SQLite data..."
docker run --rm --entrypoint "python" \
  -e DEBUG=1 \
  -e DATABASE_URL=sqlite:////app/db.sqlite3 \
  -e "SECRET_KEY=$SECRET" \
  -e ALLOWED_HOSTS=localhost \
  -v "$(pwd):/app" \
  -w /app \
  extrapaints-web:latest \
  manage.py dumpdata \
    --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission \
    -o /app/extrapaints-data.json

mv .env.production.bak .env

if [ -f extrapaints-data.json ]; then
  echo "Done:"
  ls -lh extrapaints-data.json
else
  echo "Error: extrapaints-data.json was not created"
  exit 1
fi
