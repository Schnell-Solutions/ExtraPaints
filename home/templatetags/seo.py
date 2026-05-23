from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def absolute_static(request, path):
    """Build an absolute URL for a path served by {% static %}."""
    rel = static(path)
    return request.build_absolute_uri(rel)


@register.simple_tag
def absolute_media(request, file_field):
    """Absolute URL for an ImageField/FileField value (or empty string)."""
    if not file_field:
        return ''
    try:
        url = file_field.url
    except ValueError:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    return request.build_absolute_uri(url)


@register.simple_tag
def json_ld_script(json_string):
    """Emit a safe JSON-LD script block (empty string if no data)."""
    if not json_string:
        return ''
    return mark_safe(f'<script type="application/ld+json">{json_string}</script>')


@register.simple_tag
def thumbnail(field, width=400):
    """Optimized image URL for templates."""
    try:
        from core.images import thumbnail_url
        return thumbnail_url(field, width=int(width))
    except Exception:
        if not field:
            from core.images import _catalog_placeholder_url
            return _catalog_placeholder_url()
        try:
            return field.url
        except ValueError:
            from core.images import _catalog_placeholder_url
            return _catalog_placeholder_url()


@register.inclusion_tag('partials/responsive_image.html')
def responsive_img(
    file_field=None,
    *,
    src='',
    alt='',
    css_class='',
    width=None,
    height=None,
    lazy=True,
    sizes='(max-width: 768px) 100vw, 50vw',
    request=None,
):
    image_src = src
    if file_field and not image_src:
        try:
            image_src = file_field.url
            if request and image_src.startswith('/'):
                image_src = request.build_absolute_uri(image_src)
        except ValueError:
            image_src = ''
    return {
        'src': image_src,
        'alt': alt,
        'css_class': css_class,
        'width': width,
        'height': height,
        'lazy': lazy,
        'sizes': sizes,
    }
