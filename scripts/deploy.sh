#!/bin/sh
# Production deploy / update — run on the server from the project root.
# Usage: ./scripts/deploy.sh
#        ./scripts/deploy.sh --pull   # git pull then rebuild

set -e
cd "$(dirname "$0")/.."

if [ "$1" = "--pull" ]; then
  echo "Pulling latest code..."
  git pull origin main
fi

echo "Building and starting containers..."
docker compose \
  -f docker-compose.yml \
  -f docker-compose.production.yml \
  -p extrapaints \
  up -d --build

echo ""
docker compose -p extrapaints ps
echo ""
echo "Done. Logs: docker compose -p extrapaints logs -f web"
