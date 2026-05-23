# Fresh production setup (keep backups, clean server)

Use this when you want a **clean, professional** install at `/home/james/extrapaints` with **Git + Docker**, while **keeping** `/home/james/backups/`.

**Never delete:** `/home/james/backups/`

---

## Final layout

```
/home/james/
├── backups/
│   └── extrapaints-YYYYMMDD/    # KEEP — db.sqlite3, .env, media/
└── extrapaints/                   # Fresh Git clone — only place you deploy
```

**Updates later:** `cd /home/james/extrapaints && ./scripts/deploy.sh --pull`

---

# PART 1 — Clean the server (keep backups)

SSH in:

```bash
ssh root@173.249.15.15
```

## 1.1 Extra safety backup (media volume → tar)

```bash
mkdir -p /home/james/backups/extrapaints-final-$(date +%Y%m%d)

docker run --rm \
  -v extrapaints_media_volume:/media:ro \
  -v /home/james/backups/extrapaints-final-$(date +%Y%m%d):/backup \
  alpine tar czf /backup/media-volume.tar.gz -C /media .

ls -lh /home/james/backups/extrapaints-final-$(date +%Y%m%d)/media-volume.tar.gz
```

## 1.2 Stop and remove old containers

```bash
cd /home/james/extrapaints 2>/dev/null || true
docker compose down 2>/dev/null || true
docker compose -p extrapaints down 2>/dev/null || true
docker rm -f extrapaints_web extrapaints_nginx extrapaints_db extrapaints_redis 2>/dev/null || true
docker ps -a
```

## 1.3 Move old project folder (do not delete backups)

```bash
cd /home/james
mv extrapaints extrapaints-old-$(date +%Y%m%d) 2>/dev/null || true
ls -la /home/james/
ls -la /home/james/backups/
```

Confirm backups still exist:

```bash
ls -la /home/james/backups/extrapaints-*/
```

## 1.4 (Optional) Remove old Docker volumes

**Only after** `media-volume.tar.gz` and `db.sqlite3` are in backups:

```bash
docker volume rm extrapaints_media_volume extrapaints_postgres_data extrapaints_static_volume 2>/dev/null || true
docker volume ls
```

Skip this step if unsure — old volumes do not hurt a fresh clone.

---

# PART 2 — Fresh install from Git

## 2.1 Push code from your PC (once)

On Windows:

```bash
cd "C:\Users\user\Desktop\CodeWizard\SchnellSolutionsProjects\Extra Paints\ExtraPaints"
git push origin main
```

## 2.2 Clone on server

```bash
cd /home/james
git clone https://github.com/YOUR_USER/ExtraPaints.git extrapaints
cd extrapaints
chmod +x scripts/deploy.sh
```

Replace `YOUR_USER/ExtraPaints` with your real repository URL.

## 2.3 Restore data from backup

Pick your backup folder name:

```bash
BACKUP=/home/james/backups/extrapaints-20250522   # change date if different

cp "$BACKUP/db.sqlite3" /home/james/extrapaints/
cp -r "$BACKUP/media" /home/james/extrapaints/ 2>/dev/null || true

# If media was only in tar:
# tar xzf /home/james/backups/extrapaints-final-*/media-volume.tar.gz -C /home/james/extrapaints/media
```

```bash
mkdir -p /home/james/extrapaints/media
ls /home/james/extrapaints/media/
ls -lh /home/james/extrapaints/db.sqlite3
```

## 2.4 Create production `.env`

```bash
cp .env.production.example .env
nano .env
```

Fill in real values from your backup `.env`:

- `SECRET_KEY` — use `$$` for each `$` character (Docker Compose)
- `POSTGRES_PASSWORD` — new strong password (first install) or keep if reusing volume
- `EMAIL_HOST_PASSWORD` — no quotes
- `MEDIA_HOST_PATH=/home/james/extrapaints/media`

---

# PART 3 — Import SQLite → Postgres, then go live

## 3.1 Export SQLite (Docker — no host Django needed)

```bash
cd /home/james/extrapaints
SECRET=$(grep ^SECRET_KEY= .env | cut -d= -f2-)

docker compose -f docker-compose.yml build web

docker compose run --rm --no-deps --entrypoint "" \
  --env-file /dev/null \
  -e DEBUG=1 \
  -e DATABASE_URL=sqlite:////app/db.sqlite3 \
  -e SECRET_KEY="$SECRET" \
  -e ALLOWED_HOSTS=localhost \
  -v /home/james/extrapaints:/app \
  -w /app \
  web python manage.py dumpdata \
    --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission \
    -o /app/extrapaints-data.json

ls -lh extrapaints-data.json
```

## 3.2 Start Postgres + Redis, migrate, import

```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d db redis
sleep 15

docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints run --rm \
  --entrypoint "" web python manage.py migrate --noinput

docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints run --rm \
  -v /home/james/extrapaints/extrapaints-data.json:/tmp/data.json:ro \
  --entrypoint "" web python manage.py loaddata /tmp/data.json
```

## 3.3 Start full site

```bash
./scripts/deploy.sh
```

Or manually:

```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d --build
```

## 3.4 Verify

```bash
docker compose -p extrapaints ps
docker compose -p extrapaints exec web python manage.py shell -c "
from products.models import Product
print('Products:', Product.objects.count())
"
```

Browser: https://www.extrapaints.co.ke/ and /admin/

---

# PART 4 — Easy updates (after go-live)

```bash
cd /home/james/extrapaints
./scripts/deploy.sh --pull
```

That runs `git pull` + rebuild + restart. Migrations run automatically on container start.

**Never run:** `docker compose down -v`

---

# Troubleshooting

| Issue | Fix |
|-------|-----|
| `uz` variable warning | Escape `$` as `$$` in `.env` |
| Empty products after loaddata | Re-run 3.1–3.2; check `extrapaints-data.json` size |
| Images 404 | `ls media/products/` — restore from backup tar |
| nginx SSL error | `ls /etc/letsencrypt/live/extrapaints.co.ke/` |

---

# Remove old folder (only when happy)

```bash
rm -rf /home/james/extrapaints-old-*
```

Keep `/home/james/backups/` forever or move to off-server storage.
