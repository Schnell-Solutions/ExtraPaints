#!/usr/bin/env python3
"""
Export every table from legacy db.sqlite3 to CSV files (open in Excel).

Usage (on server or PC):
  python3 scripts/export_sqlite_to_csv.py db.sqlite3
  python3 scripts/export_sqlite_to_csv.py db.sqlite3 -o data/legacy_export

No Django required — only Python 3 + sqlite3.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


def export_db(db_path: Path, out_dir: Path) -> None:
    if not db_path.is_file():
        raise SystemExit(f"Database not found: {db_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

        print(f"Exporting {len(tables)} tables from {db_path} -> {out_dir}\n")
        for (table_name,) in tables:
            rows = conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
            csv_path = out_dir / f"{table_name}.csv"
            if not rows:
                cols = [d[1] for d in conn.execute(f'PRAGMA table_info("{table_name}")')]
                with csv_path.open("w", newline="", encoding="utf-8") as fh:
                    csv.writer(fh).writerow(cols)
                print(f"  {table_name}: 0 rows (empty)")
                continue

            fieldnames = rows[0].keys()
            with csv_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: row[k] for k in fieldnames})
            print(f"  {table_name}: {len(rows)} rows -> {csv_path.name}")

        readme = out_dir / "README.txt"
        readme.write_text(
            "Legacy SQLite export — see LEGACY-DATA-IMPORT.md\n"
            "  docker compose exec web python manage.py import_legacy_csv "
            "--dir data/legacy_export --dry-run\n"
            "  docker compose exec web python manage.py import_legacy_csv "
            "--dir data/legacy_export --step all\n",
            encoding="utf-8",
        )
        print(f"\nDone. Open CSV files in Excel from: {out_dir}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Export SQLite tables to CSV")
    parser.add_argument("database", type=Path, help="Path to db.sqlite3")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data/legacy_export"),
        help="Output directory for CSV files",
    )
    args = parser.parse_args()
    export_db(args.database.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
