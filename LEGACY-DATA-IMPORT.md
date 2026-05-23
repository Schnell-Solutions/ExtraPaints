# Legacy data import (schema changed — safe CSV path)

Use this when the **new models differ** from old production SQLite. Do not use `dumpdata`/`loaddata` across versions.

## Strategy

| Layer | What happens |
|-------|----------------|
| **Export** | Raw SQLite → CSV (old columns only) |
| **Review** | Edit CSVs in Excel if needed |
| **Import** | Scripts map old rows → **new** models; new fields get defaults |
| **Skip** | Tables that never existed (AuthOTP, affiliates, guides…) |
| **Media** | File paths kept if files exist under `media/` |

## What is NOT imported automatically

- `affiliates_*` — new app (add in admin later)
- `guides_*` — new app (seed or admin)
- `accounts_accountdeletionrequest`, `accounts_authotp` — did not exist in old DB
- Customer **saved** favorites / quote sessions — re-created by users over time

## What IS imported

- Categories, colors, products (+ colour/size links if CSV exists)
- Ideas + gallery images
- Portfolio + gallery images
- Users (optional `--step users`) — keeps password hash if in CSV

---

## Step 1 — Export on your PC (from backup `db.sqlite3`)

```bash
cd ExtraPaints
python scripts/export_sqlite_to_csv.py C:\Users\user\Desktop\extrapaints-backup\db.sqlite3 -o data/legacy_export
```

Check `data/legacy_export/products_product.csv`, `colors_color.csv`, etc.

---

## Step 2 — Copy CSVs to server

```powershell
scp -r data\legacy_export root@173.249.15.15:/home/james/extrapaints/data/
```

---

## Step 3 — Site must be running (empty Postgres OK)

```bash
cd /home/james/extrapaints
docker compose -p extrapaints ps   # web + db up
```

`media/` must contain image files (paths in CSV must match).

---

## Step 4 — Dry run (no changes)

```bash
docker compose -p extrapaints exec web python manage.py import_legacy_csv \
  --dir data/legacy_export --step all --dry-run
```

Read counts and warnings.

---

## Step 5 — Import for real (order matters)

```bash
docker compose -p extrapaints exec web python manage.py import_legacy_csv \
  --dir data/legacy_export --step all
```

Or one step at a time:

```bash
docker compose -p extrapaints exec web python manage.py import_legacy_csv --dir data/legacy_export --step categories
docker compose -p extrapaints exec web python manage.py import_legacy_csv --dir data/legacy_export --step colors
docker compose -p extrapaints exec web python manage.py import_legacy_csv --dir data/legacy_export --step products
docker compose -p extrapaints exec web python manage.py import_legacy_csv --dir data/legacy_export --step ideas
docker compose -p extrapaints exec web python manage.py import_legacy_csv --dir data/legacy_export --step portfolio
```

Optional staff/customers:

```bash
docker compose -p extrapaints exec web python manage.py import_legacy_csv --dir data/legacy_export --step users
```

---

## Step 6 — Verify

```bash
docker compose -p extrapaints exec web python manage.py shell -c "
from products.models import Product
from colors.models import Color
print('Products', Product.objects.count())
print('Colors', Color.objects.count())
"
```

Browser: product pages, images, admin list counts.

---

## If a column was renamed or added

- **Old CSV column missing** → new field uses model default (OK).
- **New required field** → import sets a sensible default in code.
- **Wrong image path** → row imports without image; fix CSV path or copy file into `media/`, re-run `--step products`.

## Re-import safely

Imports use `update_or_create` on slug/code/username — you can re-run a step after fixing CSVs.

To start completely fresh (destructive):

```bash
docker compose -p extrapaints exec web python manage.py flush --no-input
# then import again
```

Only `flush` if you intend to wipe all DB data.
