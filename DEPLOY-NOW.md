# Deploy now (empty database, keep media + email) — data later

Use this plan when you want the **new site live first** and will add catalog/users **later**.

---

## What you keep on the server

| Keep | Purpose |
|------|---------|
| `media/` | Product/images (already uploaded) |
| `.env` | Email, secrets, domain settings |
| TLS certs | HTTPS |

## What you download to your PC (archive only)

| File | Why |
|------|-----|
| `db.sqlite3` | Old data — work on import later |
| `.env` backup | Reference |
| `media-volume.tar.gz` | Extra backup of images |

## What you skip for now

- SQLite → Postgres export/import
- `loaddata` / `dumpdata`
- Filling products in admin (until later)

---

## Step 1 — Download backups to your PC

On your **Windows PC** (PowerShell):

```powershell
scp root@173.249.15.15:/home/james/backups/extrapaints-20260522/db.sqlite3 "$env:USERPROFILE\Desktop\extrapaints-backup\"
scp root@173.249.15.15:/home/james/backups/extrapaints-20260522/.env "$env:USERPROFILE\Desktop\extrapaints-backup\"
scp root@173.249.15.15:/home/james/backups/extrapaints-final-20260523/media-volume.tar.gz "$env:USERPROFILE\Desktop\extrapaints-backup\"
```

Create the folder first: `mkdir Desktop\extrapaints-backup`

---

## Step 2 — Production `.env` on server (no SQLite)

```bash
nano /home/james/extrapaints/.env
```

Must have:

```env
DEBUG=0
SECRET_KEY=...   ($ as $$ for Docker)
ALLOWED_HOSTS=173.249.15.15,extrapaints.co.ke,www.extrapaints.co.ke
CSRF_TRUSTED_ORIGINS=https://extrapaints.co.ke,https://www.extrapaints.co.ke

POSTGRES_DB=extrapaints
POSTGRES_USER=extrapaints
POSTGRES_PASSWORD=<strong-password>

MEDIA_HOST_PATH=/home/james/extrapaints/media
CACHE_URL=redis://redis:6379/1

USE_SECURE_PROXY=1
SECURE_SSL_REDIRECT=0
PUBLIC_SITE_URL=https://www.extrapaints.co.ke
TAILWIND_CDN=0

EMAIL_HOST=mail.extrapaints.co.ke
EMAIL_PORT=465
EMAIL_HOST_USER=info@extrapaints.co.ke
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=ExtraPaints <info@extrapaints.co.ke>
SALES_TEAM_EMAIL=sales@extrapaints.co.ke
ADMIN_EMAIL=jamesmatata@schnell.solutions
```

**Remove:** `DATABASE_URL=sqlite:///...` and `DJANGO_SUPERUSER_*`

---

## Step 3 — Start the site (empty Postgres)

```bash
cd /home/james/extrapaints

docker compose \
  -f docker-compose.yml \
  -f docker-compose.production.yml \
  -p extrapaints \
  up -d --build
```

Entrypoint runs **migrate** automatically (empty tables, ready for later data).

```bash
docker compose -p extrapaints logs -f web
docker compose -p extrapaints ps
```

---

## Step 4 — New admin user

```bash
docker compose -p extrapaints exec web python manage.py createsuperuser
```

---

## Step 5 — Test

- https://www.extrapaints.co.ke/ — homepage (catalog may be empty)
- https://www.extrapaints.co.ke/admin/ — login
- Contact form / quote — test **email** arrives
- Image URL: https://www.extrapaints.co.ke/media/... (if you know a file path)

---

## Later — when you are ready for data

1. On PC: `python3 scripts/export_sqlite_to_csv.py db.sqlite3` (from your downloaded backup)
2. Edit CSVs in Excel
3. Import via admin or future import scripts
4. Or add products manually in admin

Your `db.sqlite3` on your PC is the source of truth until then.

---

## Updates (after go-live)

```bash
cd /home/james/extrapaints
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d --build
```

**Never:** `docker compose down -v`
