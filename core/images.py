"""On-demand image thumbnails (WebP when supported) to avoid serving full uploads."""

import hashlib
from io import BytesIO
from pathlib import Path

from django.conf import settings


def thumbnail_url(file_field, *, width=400, quality=82):
    """
    Return URL for a resized derivative cached under MEDIA_ROOT/thumbs/.
    Falls back to original URL if Pillow is unavailable or processing fails.
    """
    if not file_field:
        return ''

    try:
        original_path = Path(file_field.path)
    except (ValueError, AttributeError):
        return file_field.url

    if not original_path.exists():
        return file_field.url

    ext = '.webp'
    digest = hashlib.sha256(f'{original_path}:{width}:{quality}'.encode()).hexdigest()[:16]
    thumb_dir = Path(settings.MEDIA_ROOT) / 'thumbs' / str(width)
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = thumb_dir / f'{digest}{ext}'
    thumb_url = f'{settings.MEDIA_URL.rstrip("/")}/thumbs/{width}/{digest}{ext}'

    if thumb_path.exists():
        return thumb_url

    try:
        from PIL import Image
    except ImportError:
        return file_field.url

    try:
        with Image.open(original_path) as img:
            img = img.convert('RGB')
            w_percent = width / float(img.size[0])
            height = int(float(img.size[1]) * w_percent)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format='WEBP', quality=quality, method=6)
            thumb_path.write_bytes(buffer.getvalue())
        return thumb_url
    except Exception:
        return file_field.url


def thumbnail_for_image_url(image_url, *, width=400):
    """Best-effort thumbnail when only a URL string is available (e.g. idea display URL)."""
    if not image_url or not image_url.startswith('/media/'):
        return image_url
    rel = image_url[len('/media/'):]
    media_path = Path(settings.MEDIA_ROOT) / rel
    if not media_path.exists():
        return image_url

    class _PseudoField:
        path = str(media_path)
        url = image_url

    return thumbnail_url(_PseudoField(), width=width)
