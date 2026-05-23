"""Helpers for legacy CSV import (old SQLite schema -> new Django models)."""
import csv
from pathlib import Path

from django.conf import settings


def read_csv(data_dir: Path, table_name: str) -> list[dict]:
    path = data_dir / f"{table_name}.csv"
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def as_bool(val, default=False) -> bool:
    if val is None or val == "":
        return default
    return str(val).strip().lower() in ("1", "true", "yes")


def as_int(val, default=None):
    if val is None or val == "":
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def slugify_fallback(value: str, max_len: int = 160) -> str:
    from django.utils.text import slugify

    base = slugify(value) or "item"
    return base[:max_len]


def media_file_field(relative: str) -> str:
    """Return relative media path only if the file exists on disk."""
    relative = (relative or "").strip()
    if not relative:
        return ""
    if (Path(settings.MEDIA_ROOT) / relative).is_file():
        return relative
    return ""


def pick(row: dict, *keys, default=""):
    """First matching column from legacy export (handles minor renames)."""
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return default
