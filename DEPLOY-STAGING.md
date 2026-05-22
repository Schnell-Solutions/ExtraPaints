# Staging deployment (alongside old production)

Deploy the **new** ExtraPaints into `/opt/extrapaints-staging` on port **8080**.
Your **old live site** stays on ports **80/443** until you cut over.

---

## Overview

| | Old production | New staging |
|--|----------------|-------------|
| Folder | (existing — do not change) | `/opt/extrapaints-staging` |
| Ports | 80 / 443 | **8080** (HTTP) |
| Database | (existing) | New Postgres volume (isolated) |
| Docker project | (existing) | `extrapaints-staging` |

---

## Step 1 — On your PC (before server)

### 1.1 Commit and push the new code

```bash
git add .
git commit -m "Staging deploy: Docker, Postgres, production settings"
git push origin main
```

### 1.2 Prepare staging environment file

Copy `.env.staging.example` to a local file `staging.env` and fill in:

- `YOUR_SERVER_IP` — VPS public IP
- `SECRET_KEY` — new random secret (not the same as production)
- `POSTGRES_PASSWORD` — strong password
- Email SMTP settings (can use same server as prod; use a distinct `DEFAULT_FROM_EMAIL` label)

You will upload this to the server as `/opt/extrapaints-staging/.env`.

**Keep your local dev `.env` unchanged** (`DEBUG=1`, SQLite).

---

## Step 2 — Server: create staging folder

SSH into the VPS (same server as old production):

```bash
ssh user@YOUR_SERVER_IP
```

Create the staging directory (separate from old app):

```bash
sudo mkdir -p /opt/extrapaints-staging
sudo chown $USER:$USER /opt/extrapaints-staging
cd /opt/extrapaints-staging
```

Clone the **new** codebase:

```bash
git clone https://github.com/YOUR_ORG/ExtraPaints.git .
# or: git clone <your-repo-url> .
```

---

## Step 3 — Server: staging `.env`

```bash
nano /opt/extrapaints-staging/.env
```

Paste contents from your prepared `staging.env`. Minimum required:

- `DEBUG=0`
- `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `EMAIL_*` and `DEFAULT_FROM_EMAIL`
- `PUBLIC_SITE_URL=http://YOUR_SERVER_IP:8080`

Save and exit.

---

## Step 4 — Open port 8080 (firewall)

If `ufw` is enabled:

```bash
sudo ufw allow 8080/tcp
sudo ufw status
```

Do **not** stop or change rules for 80/443 (old production).

---

## Step 5 — Build and start staging

```bash
cd /opt/extrapaints-staging

docker compose \
  -f docker-compose.yml \
  -f docker-compose.staging.yml \
  -p extrapaints-staging \
  up -d --build
```

Watch startup:

```bash
docker compose -p extrapaints-staging logs -f web
```

Wait until you see migrations, collectstatic, and Gunicorn running.

---

## Step 6 — Create staging admin user

```bash
docker compose -p extrapaints-staging exec web python manage.py createsuperuser
```

---

## Step 7 — Test staging

In a browser:

```
http://YOUR_SERVER_IP:8080/
http://YOUR_SERVER_IP:8080/admin/
http://YOUR_SERVER_IP:8080/robots.txt
```

Checklist:

- [ ] Homepage loads with styles (Tailwind compiled CSS)
- [ ] Admin login works
- [ ] Contact / quote form (test email)
- [ ] Register + OTP email (if enabled)

Optional — copy dev media into staging:

```bash
# From your PC
scp -r media user@YOUR_SERVER_IP:/tmp/media-staging
# On server
docker compose -p extrapaints-staging cp /tmp/media-staging/. web:/app/media/
```

---

## Step 8 — (Optional) Staging subdomain

When ready, add DNS:

| Type | Name | Value |
|------|------|--------|
| A | `staging` | `YOUR_SERVER_IP` |

Update `.env`:

```env
ALLOWED_HOSTS=extrapaints.co.ke,staging.extrapaints.co.ke,YOUR_SERVER_IP
CSRF_TRUSTED_ORIGINS=http://staging.extrapaints.co.ke:8080
PUBLIC_SITE_URL=http://staging.extrapaints.co.ke:8080
```

Restart:

```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml -p extrapaints-staging up -d
```

---

## Step 9 — Later: cut over to production

When staging is approved:

1. **Backup** old production DB and files.
2. **Maintenance window** — brief downtime or blue/green switch.
3. Options:
   - **A)** Stop old app → deploy new app in main folder on 80/443 with production `.env` and `docker compose` (no staging overlay).
   - **B)** Point nginx on 80/443 to staging stack after switching `docker-compose.staging.yml` ports to 80/443.
4. **Migrate data** from old DB/media into new Postgres/volumes if needed (not automatic).
5. Smoke-test live domain.

---

## Useful commands

```bash
# Status
docker compose -p extrapaints-staging ps

# Logs
docker compose -p extrapaints-staging logs -f web nginx

# Restart after .env change
docker compose -f docker-compose.yml -f docker-compose.staging.yml -p extrapaints-staging up -d

# Pull updates
cd /opt/extrapaints-staging && git pull
docker compose -f docker-compose.yml -f docker-compose.staging.yml -p extrapaints-staging up -d --build

# Stop staging (does not affect old production)
docker compose -p extrapaints-staging down
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 8080 in use | `sudo ss -tlnp \| grep 8080` — change port in `docker-compose.staging.yml` |
| 502 on :8080 | `docker compose -p extrapaints-staging logs web` |
| CSRF error | Match `CSRF_TRUSTED_ORIGINS` to exact URL including `:8080` |
| Disallowed host | Add IP/domain to `ALLOWED_HOSTS` |
| Old site broken | You only changed `/opt/extrapaints-staging` — old app is separate |
