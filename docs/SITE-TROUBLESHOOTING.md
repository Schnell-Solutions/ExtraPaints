# Site not loading (domain shows blank / directory listing)

## Symptom: “Index of /” or LiteSpeed page

If https://www.extrapaints.co.ke shows **“Index of /”** and **LiteSpeed Web Server**, the domain is **not** hitting your Docker **nginx** container. Another web server on the VPS took ports 80/443.

ExtraPaints should be served by:

`docker compose … → extrapaints_nginx → web:8000`

## Quick checks (on the server as root)

```bash
cd /home/james/extrapaints

# 1) Are containers running?
docker compose -p extrapaints ps

# 2) Who owns ports 80 and 443?
ss -tlnp | grep -E ':80 |:443 '

# 3) Test Docker nginx locally (should return HTML, not "Index of /")
curl -sI -H "Host: www.extrapaints.co.ke" http://127.0.0.1/ | head -5
```

## Fix A — Stop LiteSpeed (or host Apache) so Docker nginx can bind 80/443

Common on VPS panels (CyberPanel, OpenLiteSpeed, etc.):

```bash
systemctl stop lsws 2>/dev/null || systemctl stop openlitespeed 2>/dev/null || true
systemctl disable lsws 2>/dev/null || true

cd /home/james/extrapaints
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d nginx web
```

Confirm:

```bash
curl -sI https://www.extrapaints.co.ke | head -5
# Expect: HTTP/2 200 and NO "LiteSpeed" in headers/body
```

## Fix B — Keep LiteSpeed but reverse-proxy to Docker

Point the vhost for `extrapaints.co.ke` to proxy `http://127.0.0.1:8080` only if you move Docker nginx to 8080 (advanced; Fix A is simpler).

## Fix C — Containers stopped

```bash
cd /home/james/extrapaints
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d
docker compose -p extrapaints logs nginx --tail 30
docker compose -p extrapaints logs web --tail 30
```

## After the site is back

Deploy latest code:

```bash
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.production.yml -p extrapaints up -d --build web nginx
```
