# Production deployment (Docker Compose)

## Prerequisites

- Docker and Docker Compose on the server
- DNS pointing to the server for `extrapaints.co.ke` / `www.extrapaints.co.ke`
- TLS certificates under `/etc/letsencrypt` (see nginx `default.conf`)

## First-time setup

1. Copy `.env.example` to `.env` and fill in production values (especially `SECRET_KEY`, `POSTGRES_PASSWORD`, email).
2. Build and start:

   ```bash
   docker compose up -d --build
   ```

3. Create an admin user:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

4. (Optional) Warm image thumbnails:

   ```bash
   docker compose exec web python manage.py warm_thumbnails
   ```

The `web` entrypoint runs database migrations and `collectstatic` on every container start.

## Volumes

| Volume | Purpose |
|--------|---------|
| `postgres_data` | PostgreSQL data |
| `static_volume` | Collected static files (nginx + gunicorn) |
| `media_volume` | User uploads and generated thumbnails |

Back up `postgres_data` and `media_volume` regularly.

## Local development

Keep `DEBUG=1` and `DATABASE_URL=sqlite:///db.sqlite3` in `.env` for `manage.py runserver`.

Do not use `docker compose` without `POSTGRES_PASSWORD` unless you add production vars to `.env`.
