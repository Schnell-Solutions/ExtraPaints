#!/bin/sh
set -e

# Named volumes may be root-owned on first run; ensure app can write static/media/logs.
chown -R app:app /app/static /app/media /app/logs 2>/dev/null || true
# Host bind mounts (MEDIA_HOST_PATH) keep host ownership; ensure thumbs are writable.
mkdir -p /app/media/thumbs
chmod -R a+rwX /app/media/thumbs 2>/dev/null || true

echo "Waiting for database..."
python <<'PY'
import os
import sys
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ExtraPaints.settings")
django.setup()

from django.db import connection
from django.db.utils import OperationalError

for attempt in range(30):
    try:
        connection.ensure_connection()
        break
    except OperationalError:
        if attempt == 29:
            sys.exit(1)
        time.sleep(1)
else:
    sys.exit(1)
PY

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput
chown -R app:app /app/static 2>/dev/null || true

echo "Starting Gunicorn..."
exec runuser -u app -- gunicorn ExtraPaints.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
