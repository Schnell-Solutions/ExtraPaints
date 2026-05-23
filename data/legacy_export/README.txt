Legacy SQLite export — see LEGACY-DATA-IMPORT.md
  docker compose exec web python manage.py import_legacy_csv --dir data/legacy_export --dry-run
  docker compose exec web python manage.py import_legacy_csv --dir data/legacy_export --step all
