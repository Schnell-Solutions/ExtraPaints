# Production upgrade (keep existing database + media)

> **Full operations guide:** see [docs/OPERATIONS-GUIDE.md](docs/OPERATIONS-GUIDE.md)

Use this when you already copied old production data and want to **update the code** without wiping DB or uploads.

---

## Golden rules

| Do | Don't |
|----|--------|
| `docker compose down` | `docker compose down -v` (**deletes** named volumes) |
| Backup DB + media before upgrade | Delete `media/` or Postgres data folders |
| `migrate` (adds/updates tables only) | `flush`, drop database, or new empty `POSTGRES_PASSWORD` on old volume |
| Same `POSTGRES_*` / `DATABASE_URL` as current DB | New random DB password on an existing Postgres volume |

---

## What the new code does to your data

- **`migrate`** — updates schema; does **not** delete products/users/media rows.
- **`collectstatic`** — refreshes CSS/JS in `static/` only; does **not** touch `media/`.
- **Media volume/folder** — mounted read/write; files stay on disk.
- **Postgres volume/folder** — same data if you reuse path/credentials.

---

## Migrate SQLite to Postgres (one-time — old production used `db.sqlite3`)

Your previous `.env` had `DATABASE_URL=sqlite:///db.sqlite3`. The new app **cannot** use SQLite when `DEBUG=0`.

**On the server** (with `db.sqlite3` and `media/` in the project folder):

```bash
cd /opt/extrapaints

# 1) Export data from SQLite (use old code OR temporary DEBUG=1 — see below)
# If only new code is present, copy db.sqlite3 and run export with DEBUG=1 once:
export DEBUG=1
export DATABASE_URL=sqlite:///db.sqlite3
export SECRET_KEY=your-secret-key
python manage.py dumpdata \
  --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission \
  -o /tmp/extrapaints-data.json

# 2) Start Postgres (new stack) without web yet, or full stack:
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d db redis
# Set POSTGRES_* in .env first (see .env.production.example)

# 3) Migrate empty Postgres schema
docker compose -p extrapaints run --rm web python manage.py migrate --noinput

# 4) Load data into Postgres
docker compose -p extrapaints run --rm web python manage.py loaddata /tmp/extrapaints-data.json
# (copy JSON into container if needed: docker compose cp /tmp/extrapaints-data.json web:/tmp/)

# 5) Full production up with DEBUG=0 in .env
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d --build
```

Keep `db.sqlite3` as backup; do not delete until the site is verified.

**Admin login:** Your old `admin` user comes from this import — you do **not** need `DJANGO_SUPERUSER_*` variables.

---

## Step 1 — Backup (mandatory, 10 minutes)

On the server, in your **production** folder:

```bash
cd /opt/extrapaints   # your real path — adjust if different
```

**Database backup**

```bash
# If using Docker Postgres from this project:
docker compose exec db pg_dump -U extrapaints extrapaints > ~/backup-$(date +%Y%m%d)-db.sql

# If Postgres runs on the host (not in compose):
pg_dump -U YOUR_USER YOUR_DB > ~/backup-$(date +%Y%m%d)-db.sql
```

**Media backup**

```bash
tar -czf ~/backup-$(date +%Y%m%d)-media.tar.gz media/
# or, if media is only in Docker volume:
docker compose cp web:/app/media ./media-backup
tar -czf ~/backup-$(date +%Y%m%d)-media.tar.gz media-backup/
```

Keep these files until the new site is stable for several days.

---

## Step 2 — On your PC: push new code

```bash
git add .
git commit -m "Production upgrade: preserve DB and media"
git push origin main
```

---

## Step 3 — On the server: update code (do not delete data)

```bash
cd /opt/extrapaints   # same folder where old production lives
git pull
```

If you **copied** old production into this folder manually, merge so you have:

- New code from Git (`git pull` or copy new files over **except** `media/`, `.env`, and postgres data)
- **Untouched:** `media/` (or your media path), `.env`, Postgres data directory/volume

---

## Step 4 — Production `.env`

Edit `.env` (copy from `.env.production.example` if needed):

```bash
nano .env
```

Required for production:

```env
DEBUG=0
SECRET_KEY=<strong-secret>
ALLOWED_HOSTS=extrapaints.co.ke,www.extrapaints.co.ke
CSRF_TRUSTED_ORIGINS=https://extrapaints.co.ke,https://www.extrapaints.co.ke

# MUST match your EXISTING database (same user/password/db name):
POSTGRES_DB=extrapaints
POSTGRES_USER=extrapaints
POSTGRES_PASSWORD=<your-current-db-password>

# If media lives on disk (you copied production media here):
MEDIA_HOST_PATH=/opt/extrapaints/media

# If Postgres data lives on disk (not only Docker volume):
# POSTGRES_HOST_PATH=/opt/extrapaints/postgres-data

USE_SECURE_PROXY=1
SECURE_SSL_REDIRECT=0
PUBLIC_SITE_URL=https://www.extrapaints.co.ke
TAILWIND_CDN=0

EMAIL_HOST=...
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=...
```

**If old DB is external**, set `DATABASE_URL` instead of relying on the `db` service and use the same database name as before.

---

## Step 5 — Stop old app only (keep volumes)

**Old setup is Docker:**

```bash
cd /opt/extrapaints
docker compose down
# NO -v flag
```

**Old setup is not Docker** (nginx + gunicorn on host): stop those services, but **do not** delete `media/` or Postgres files.

```bash
sudo systemctl stop nginx   # or your old service names
# leave data directories alone
```

---

## Step 6 — Build and start new stack (reuse data)

```bash
cd /opt/extrapaints

docker compose \
  -f docker-compose.yml \
  -f docker-compose.production.yml \
  -p extrapaints \
  up -d --build
```

Use **the same** `-p extrapaints` project name you used before so Docker reuses `postgres_data` and `media_volume` if you did not set `MEDIA_HOST_PATH`.

Watch logs:

```bash
docker compose -p extrapaints logs -f web
```

Expect: wait for DB → **migrations** → collectstatic → Gunicorn.

---

## Step 7 — Verify data is still there

```bash
docker compose -p extrapaints exec web python manage.py shell -c "
from products.models import Product
from django.contrib.auth import get_user_model
print('Products:', Product.objects.count())
print('Users:', get_user_model().objects.count())
"
```

In the browser:

- `https://www.extrapaints.co.ke/` — products/images load
- `/admin/` — log in with **existing** admin (no new superuser needed if users exist)
- Open a product with an image — confirms `media/` works

**Only if you have no admin user:**

```bash
docker compose -p extrapaints exec web python manage.py createsuperuser
```

---

## Step 8 — You do NOT re-import all content

| Situation | Action |
|-----------|--------|
| DB + media reused correctly | **Nothing** — products/users/images are already there |
| Images 404 but DB OK | Fix `MEDIA_HOST_PATH` or volume mount; files must be under `/app/media` in container |
| DB empty but you have `.sql` backup | Restore backup (Step 9 below), then `migrate` |
| Missing only a few items | Add via Django admin |

---

## Step 9 — Restore only if something went wrong

**Database:**

```bash
docker compose -p extrapaints exec -T db psql -U extrapaints extrapaints < ~/backup-YYYYMMDD-db.sql
```

**Media:**

```bash
tar -xzf ~/backup-YYYYMMDD-media.tar.gz -C /opt/extrapaints/
# or copy back into container path
```

---

## Step 10 — After it is stable

- [ ] Test quote, contact, login/OTP email
- [ ] Keep backups 2–4 weeks
- [ ] Optional: `docker compose -p extrapaints exec web python manage.py warm_thumbnails`
- [ ] Remove **old** code service only after you are sure (not `media/` or DB)

---

## Quick reference: where data lives

| Data | Typical location |
|------|------------------|
| Uploads | `media/` on host **or** Docker volume `extrapaints_media_volume` |
| Postgres | Docker volume `extrapaints_postgres_data` **or** `POSTGRES_HOST_PATH` |
| Static (CSS) | Docker volume `extrapaints_static_volume` (rebuilt by collectstatic — safe) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `password authentication failed` | `POSTGRES_PASSWORD` in `.env` must match existing DB |
| Empty site, 0 products | Wrong DB or new empty volume — check `DATABASE_URL` / volume name |
| Images broken | `MEDIA_HOST_PATH` wrong; run `ls media/products` on host |
| Migration error | Send logs; may need backup restore + fix migration conflict |
| Lost data after `down -v` | Restore from Step 1 backups only |
