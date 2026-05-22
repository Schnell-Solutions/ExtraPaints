# Stage 1: compile Tailwind CSS (production — no CDN)
FROM node:20-alpine AS frontend
WORKDIR /app
COPY package.json package-lock.json* tailwind.config.js ./
RUN npm ci 2>/dev/null || npm install
COPY assets ./assets
COPY templates ./templates
COPY home ./home
COPY products ./products
COPY colors ./colors
COPY ideas ./ideas
COPY portfolio ./portfolio
COPY guides ./guides
COPY accounts ./accounts
COPY quote_request ./quote_request
RUN npm run build:css

# Stage 2: Django application
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TAILWIND_CDN=0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo libwebp7 util-linux \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /app/assets/css/tailwind.compiled.css ./assets/css/tailwind.compiled.css

RUN chmod +x /app/docker/entrypoint.sh \
    && addgroup --system app && adduser --system --ingroup app --no-create-home app \
    && mkdir -p /app/static /app/media /app/logs \
    && chown -R app:app /app

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
