from django.urls import NoReverseMatch, reverse


def build_breadcrumbs(request, *items):
    """
    Build breadcrumb trail items for templates and JSON-LD.

    Each item: (label, url_name, *url_args) or (label, None) for current page.
    Prepends Home automatically.
    """
    trail = [{'name': 'Home', 'url': reverse('home')}]
    for item in items:
        if len(item) == 2 and item[1] is None:
            trail.append({'name': item[0], 'url': None})
            continue
        label = item[0]
        url_name = item[1]
        args = item[2:] if len(item) > 2 else ()
        try:
            url = reverse(url_name, args=args)
        except NoReverseMatch:
            url = None
        trail.append({'name': label, 'url': url})
    return trail


def breadcrumbs_for_json(request, trail):
    """Absolute URLs for BreadcrumbList schema (skip current page without URL)."""
    base = request.build_absolute_uri('/').rstrip('/')
    items = []
    for i, crumb in enumerate(trail, start=1):
        url = crumb.get('url')
        if not url:
            continue
        if url.startswith('/'):
            url = f'{base}{url}'
        elif not url.startswith('http'):
            url = request.build_absolute_uri(url)
        items.append({
            '@type': 'ListItem',
            'position': i,
            'name': crumb['name'],
            'item': url,
        })
    return items
