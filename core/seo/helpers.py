"""Shared SEO view helpers."""


def schema_json_ld_blocks(*json_strings):
    """Return non-empty JSON-LD strings for separate <script> tags (valid per Google)."""
    return [s for s in json_strings if s]
