# ExtraPaints — Operations & deployment guide

This is the **main reference** for running ExtraPaints in production: updating code, redeploying, keeping data safe, SSL, DNS, and recovery.

**Production server (current setup)**

| Item | Value |
|------|--------|
| VPS path | `/home/james/extrapaints` |
| Docker project | `extrapaints` (`-p extrapaints`) |
| Domain | `https://www.extrapaints.co.ke` |
| Database | PostgreSQL 16 (Docker) |
| Media | Host folder `MEDIA_HOST_PATH=/home/james/extrapaints/media` |
| Code | GitHub `Schnell-Solutions/ExtraPaints` branch `main` |

---

## 1. Architecture (what runs where)

```
Internet → nginx (443/80) → web (Gunicorn/Django) → Postgres
                              ↓
                           Redis (cache)
```

**Compose files (always use both in production):**

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.production.yml \
  -p extrapaints \
  <command>
```

| Service | Container | Persists data? |
|---------|-----------|----------------|
| `db` | `extrapaints_db` | **Yes** — Postgres files (volume or `POSTGRES_HOST_PATH`) |
| `web` | `extrapaints_web` | No — rebuilt from Git on deploy |
| `nginx` | `extrapaints_nginx` | No — config from `./nginx/` |
| `redis` | `extrapaints_redis` | Cache only — safe to recreate |

On container start, `docker/entrypoint.sh` automatically:

1. Waits for Postgres  
2. Runs `migrate`  
3. Runs `collectstatic`  
4. Starts Gunicorn  

---

## 2. What is “data” vs “code”

| Data (keep) | Code (replace on deploy) |
|-------------|---------------------------|
| Postgres database (products, users, quotes, …) | Application in `/home/james/extrapaints` from Git |
| `/home/james/extrapaints/media/` (uploads) | Docker image `extrapaints-web` |
| `/home/james/extrapaints/.env` (secrets) | Collected static files in Docker volume `static_volume` |
| `/etc/letsencrypt/` (SSL certs on host) | |

**Golden rule:** routine updates only rebuild **web/nginx** — they do **not** wipe the database or media folder.

---

## 3. Routine code update (most common — keeps all data)

Use this after every merge to `main` (UI fixes, features, SEO, etc.).

### On the server

```bash
cd /home/james/extrapaints

# Optional: backup first (see section 4)
git pull origin main

# If pull fails due to local edits on server:
#   git stash push -m "server" -- docker/entrypoint.sh
#   git pull origin main

docker compose \
  -f docker-compose.yml \
  -f docker-compose.production.yml \
  -p extrapaints \
  up -d --build web nginx
```

Or use the script:

```bash
chmod +x scripts/deploy.sh   # once
./scripts/deploy.sh --pull
```

### Verify

```bash
docker compose -p extrapaints ps
docker compose -p extrapaints logs web --tail 40
curl -sI -k -H "Host: www.extrapaints.co.ke" https://127.0.0.1/ | head -5
```

Open the site in the browser and hard-refresh (`Ctrl+Shift+R`).

### Cache busting (CSS/JS)

After UI changes, bump in `.env`:

```env
STATIC_VERSION=4
```

Then rebuild `web` (and restart `nginx` if needed). Browsers load `/static/css/extrapaints.css?v=4`.

### When to rebuild only `web` vs all services

| Change | Command |
|--------|---------|
| Python/templates/CSS/JS | `up -d --build web` (+ `nginx` if nginx config changed) |
| `nginx/default.conf` only | `up -d nginx` |
| Postgres version / `.env` DB password | Careful — see section 8 |
| Nothing | `up -d` (no `--build`) |

---

## 4. Backups (before big changes)

Store backups under `/home/james/backups/` — **never delete this folder**.

### 4.1 Database (Postgres)

```bash
mkdir -p /home/james/backups/extrapaints-$(date +%Y%m%d)
docker compose -p extrapaints exec -T db \
  pg_dump -U extrapaints extrapaints \
  > /home/james/backups/extrapaints-$(date +%Y%m%d)/db.sql
```

### 4.2 Media files

```bash
tar czf /home/james/backups/extrapaints-$(date +%Y%m%d)/media.tar.gz \
  -C /home/james/extrapaints media
```

### 4.3 Environment & project config

```bash
cp /home/james/extrapaints/.env /home/james/backups/extrapaints-$(date +%Y%m%d)/.env
```

### 4.4 Download to your PC (optional)

```powershell
scp -r root@173.249.15.15:/home/james/backups/extrapaints-YYYYMMDD C:\Users\user\Desktop\extrapaints-backup\
```

---

## 5. Fresh redeploy (same server, keep backups)

Use when the server folder is messy, Git is out of sync, or you want a clean clone — **without losing backups**.

### 5.1 Backup (section 4)

### 5.2 Stop containers (does NOT delete data if you avoid `-v`)

```bash
cd /home/james/extrapaints
docker compose -p extrapaints stop
# Do NOT run: docker compose down -v
```

### 5.3 Refresh code

**Option A — reset Git in place**

```bash
cd /home/james/extrapaints
git fetch origin
git reset --hard origin/main
```

**Option B — new clone**

```bash
cd /home/james
mv extrapaints extrapaints-old-$(date +%Y%m%d)
git clone https://github.com/Schnell-Solutions/ExtraPaints.git extrapaints
cd extrapaints
cp ../extrapaints-old-*/.env .env    # restore secrets
chmod +x scripts/deploy.sh docker/entrypoint.sh
```

Ensure media still exists:

```bash
ls /home/james/extrapaints/media/products/main/ | head
```

### 5.4 Start stack

```bash
cd /home/james/extrapaints
docker compose \
  -f docker-compose.yml \
  -f docker-compose.production.yml \
  -p extrapaints \
  up -d --build
```

Postgres data is kept if:

- Same Docker volume name (`extrapaints_postgres_data`), **or**
- Same `POSTGRES_HOST_PATH` in `.env`, **and**
- Same `POSTGRES_PASSWORD` as when the volume was created.

---

## 6. Fresh deploy with empty database (keep media only)

Use for a clean catalog DB but existing uploads on disk.

1. Backup (section 4).  
2. Stop web: `docker compose -p extrapaints stop web`.  
3. **Only if you intend to wipe DB:** remove Postgres volume (destructive):

   ```bash
   docker compose -p extrapaints stop db
   docker volume rm extrapaints_postgres_data   # ONLY when you have db.sql backup
   ```

4. `up -d --build` — entrypoint runs migrations on empty DB.  
5. Create admin: `docker compose -p extrapaints exec web python manage.py createsuperuser`.  
6. Import catalog — see [LEGACY-DATA-IMPORT.md](../LEGACY-DATA-IMPORT.md).

Media folder is untouched if `MEDIA_HOST_PATH=/home/james/extrapaints/media` stays in `.env`.

---

## 7. Environment file (`.env`)

Copy from `.env.production.example` on first install. Critical keys:

```env
DEBUG=0
SECRET_KEY=...          # Escape $ as $$ for Docker Compose
ALLOWED_HOSTS=173.249.15.15,extrapaints.co.ke,www.extrapaints.co.ke
CSRF_TRUSTED_ORIGINS=https://extrapaints.co.ke,https://www.extrapaints.co.ke

POSTGRES_DB=extrapaints
POSTGRES_USER=extrapaints
POSTGRES_PASSWORD=<unchanged-if-reusing-db-volume>

MEDIA_HOST_PATH=/home/james/extrapaints/media
PUBLIC_SITE_URL=https://www.extrapaints.co.ke
TAILWIND_CDN=0
STATIC_VERSION=3
USE_SECURE_PROXY=1

# Email (usually still on cPanel host — do not point MX to VPS)
EMAIL_HOST=mail.extrapaints.co.ke
EMAIL_PORT=465
EMAIL_HOST_USER=info@extrapaints.co.ke
EMAIL_HOST_PASSWORD=...
```

**Do not** set `DATABASE_URL=sqlite:///...` in production.

Edit safely:

```bash
nano /home/james/extrapaints/.env
docker compose -p extrapaints up -d web   # recreate web to pick up env changes
```

---

## 8. DNS (cPanel) and SSL

### DNS (website only)

In cPanel **Zone Editor** for `extrapaints.co.ke`:

| Record | Type | Value |
|--------|------|--------|
| `@` | A | VPS IP (e.g. `173.249.15.15`) |
| `www` | A | Same VPS IP |

**Do not** change MX / `mail` / `webmail` records unless email moved to the VPS.

Verify:

```bash
dig +short www.extrapaints.co.ke
```

### SSL (Let’s Encrypt)

Certs live on the host: `/etc/letsencrypt/live/extrapaints.co.ke/`

**Renew (Docker nginx must release port 80):**

```bash
cd /home/james/extrapaints
docker compose -p extrapaints stop nginx
systemctl stop nginx    # if host nginx also binds port 80

certbot certonly --standalone \
  -d extrapaints.co.ke -d www.extrapaints.co.ke \
  --force-renewal --non-interactive

docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d nginx
systemctl disable nginx   # prefer Docker for 80/443
```

Edit `/etc/letsencrypt/renewal/extrapaints.co.ke.conf`: use `authenticator = standalone` and pre/post hooks to stop/start Docker nginx (see [SITE-TROUBLESHOOTING.md](SITE-TROUBLESHOOTING.md)).

Test auto-renew: `certbot renew --dry-run`

---

## 9. Useful maintenance commands

```bash
cd /home/james/extrapaints
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints"

# Shell / Django
$COMPOSE exec web python manage.py shell
$COMPOSE exec web python manage.py createsuperuser
$COMPOSE exec web python manage.py migrate --plan

# Catalog media check / repair
$COMPOSE exec web python manage.py verify_catalog_media
$COMPOSE exec web python manage.py verify_catalog_media --repair-from-csv --guess-missing --warm

# Legacy CSV import (see LEGACY-DATA-IMPORT.md)
$COMPOSE exec web python manage.py import_legacy_csv --dir data/legacy_export --step all

# Logs
$COMPOSE logs -f web
$COMPOSE logs nginx --tail 50

# Container health
$COMPOSE ps
ss -tlnp | grep -E ':80 |:443 '
```

---

## 10. Rollback after a bad deploy

If the new code breaks the site but the database is fine:

```bash
cd /home/james/extrapaints
git log --oneline -5
git checkout <previous-commit-sha>
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d --build web nginx
```

When stable again, fix forward on `main` and `git pull`.

**Database rollback** (only if you have `db.sql` backup):

```bash
docker compose -p extrapaints stop web
docker compose -p extrapaints exec -T db psql -U extrapaints -d extrapaints -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
cat /home/james/backups/.../db.sql | docker compose -p extrapaints exec -T db psql -U extrapaints extrapaints
docker compose -p extrapaints up -d web
```

---

## 11. Never do this in production

| Command / action | Why |
|------------------|-----|
| `docker compose down -v` | **Deletes** named volumes (Postgres, media if not bind-mounted) |
| Change `POSTGRES_PASSWORD` on existing volume | Postgres will not start — old data locked with old password |
| Delete `/home/james/extrapaints/media/` | Loses all uploads |
| Delete `/home/james/backups/` | Loses recovery copies |
| Run `flush` or drop all tables without backup | Wipes catalog and users |
| Point `@` DNS to wrong IP | Site or SSL breaks |

---

## 12. Local development → production workflow

1. Develop on PC, run tests: `python manage.py test`  
2. Commit and push to `main` on GitHub  
3. On server: section **3** (routine update)  
4. Smoke-test homepage, products, colors, admin, contact email  

**New management commands** always require `--build web` (not just restart).

---

## 13. Related docs

| Doc | When to use |
|-----|-------------|
| [SITE-TROUBLESHOOTING.md](SITE-TROUBLESHOOTING.md) | Site down, LiteSpeed, port 80 conflicts, SSL errors |
| [SEO-SITELINKS.md](SEO-SITELINKS.md) | Google Search Console, structured data |
| [LEGACY-DATA-IMPORT.md](../LEGACY-DATA-IMPORT.md) | Import old SQLite data via CSV |
| [DEPLOY-FRESH.md](../DEPLOY-FRESH.md) | Detailed first-time server cleanup steps |
| [DEPLOY-NOW.md](../DEPLOY-NOW.md) | Empty DB + existing media quick path |
| `.env.production.example` | Template for production `.env` |

---

## 14. Quick reference card

```bash
# Update code (keep data)
cd /home/james/extrapaints && git pull && ./scripts/deploy.sh

# Backup DB + media
docker compose -p extrapaints exec -T db pg_dump -U extrapaints extrapaints > ~/backups/db-$(date +%F).sql
tar czf ~/backups/media-$(date +%F).tar.gz -C /home/james/extrapaints media

# Health check
docker compose -p extrapaints ps
curl -sI https://www.extrapaints.co.ke | head -3
```

**Support checklist when something fails:** backups exist → `docker compose ps` → `logs web` → DNS → SSL → `MEDIA_HOST_PATH` → hard refresh browser.
