import json

from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags

from .breadcrumbs import breadcrumbs_for_json


def _public_root(request):
    base = getattr(settings, 'PUBLIC_SITE_URL', '').rstrip('/')
    if base:
        return base
    return request.build_absolute_uri('/').rstrip('/')


def _local_settings():
    return getattr(settings, 'SEO_LOCAL_BUSINESS', {})


def local_business_json(request):
    """PaintStore / LocalBusiness JSON-LD for Kenya local SEO."""
    cfg = _local_settings()
    root = _public_root(request)
    data = {
        '@context': 'https://schema.org',
        '@type': ['PaintStore', 'LocalBusiness', 'Store'],
        '@id': f'{root}/#localbusiness',
        'name': cfg.get('name', 'ExtraPaints'),
        'description': cfg.get(
            'description',
            'Professional paint supplier in Nairobi, Kenya — interior, exterior, and commercial '
            'coatings with tailored quotations for contractors and distributors.',
        ),
        'url': root,
        'telephone': cfg.get('telephone', []),
        'email': cfg.get('email', getattr(settings, 'BUSINESS_EMAIL', 'info@extrapaints.co.ke')),
        'image': cfg.get('image') or f'{root}/static/images/extrapaints.jpg',
        'priceRange': '$$',
        'currenciesAccepted': 'KES',
        'paymentAccepted': 'Cash, Bank Transfer, Invoice',
        'address': {
            '@type': 'PostalAddress',
            'streetAddress': cfg.get('street_address', ''),
            'addressLocality': cfg.get('city', 'Nairobi'),
            'addressRegion': cfg.get('region', 'Nairobi County'),
            'postalCode': cfg.get('postal_code', ''),
            'addressCountry': cfg.get('country', 'KE'),
        },
        'geo': {
            '@type': 'GeoCoordinates',
            'latitude': cfg.get('latitude'),
            'longitude': cfg.get('longitude'),
        },
        'areaServed': [
            {'@type': 'City', 'name': city}
            for city in cfg.get('area_served', ['Nairobi', 'Eldoret', 'Kenya'])
        ],
        'openingHoursSpecification': cfg.get('opening_hours', []),
        'sameAs': cfg.get('same_as', []),
    }
    if cfg.get('google_maps_url'):
        data['hasMap'] = cfg['google_maps_url']
    return json.dumps(data, ensure_ascii=False)


def website_search_json(request):
    root = _public_root(request)
    search_url = request.build_absolute_uri(reverse('product_list')) + '?q={search_term_string}'
    data = {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        '@id': f'{root}/#website',
        'name': 'ExtraPaints',
        'url': root,
        'description': (
            'Professional paint supply and quotation services in Nairobi and Kenya.'
        ),
        'publisher': {'@id': f'{root}/#localbusiness'},
        'potentialAction': {
            '@type': 'SearchAction',
            'target': {
                '@type': 'EntryPoint',
                'urlTemplate': search_url,
            },
            'query-input': 'required name=search_term_string',
        },
    }
    return json.dumps(data, ensure_ascii=False)


def organization_json(request):
    root = _public_root(request)
    cfg = _local_settings()
    data = {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        '@id': f'{root}/#organization',
        'name': cfg.get('name', 'ExtraPaints'),
        'url': root,
        'logo': cfg.get('logo') or f'{root}/static/images/extrapaints.jpg',
        'sameAs': cfg.get('same_as', []),
    }
    return json.dumps(data, ensure_ascii=False)


def breadcrumb_list_json(request, trail):
    elements = breadcrumbs_for_json(request, trail)
    if not elements:
        return ''
    data = {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': elements,
    }
    return json.dumps(data, ensure_ascii=False)


def product_json(request, product):
    root = _public_root(request)
    quote_url = request.build_absolute_uri(reverse('quote_detail'))
    data = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        'name': product.name,
        'sku': str(product.id),
        'brand': {'@type': 'Brand', 'name': 'ExtraPaints'},
        'category': product.category.name,
        'url': request.build_absolute_uri(product.get_absolute_url()),
    }
    desc = strip_tags(product.description or '').strip()
    if desc:
        data['description'] = desc[:5000]
    if product.main_image:
        data['image'] = [request.build_absolute_uri(product.main_image.url)]
    data['offers'] = {
        '@type': 'Offer',
        'url': quote_url,
        'availability': 'https://schema.org/PreOrder',
        'priceCurrency': 'KES',
        'seller': {'@type': 'Organization', 'name': 'ExtraPaints'},
        'description': 'Request a tailored quotation — pricing provided by sales team.',
    }
    return json.dumps(data, ensure_ascii=False)


def faq_page_json(faq_items):
    if not faq_items:
        return ''
    data = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': item['question'],
                'acceptedAnswer': {
                    '@type': 'Answer',
                    'text': item['answer'],
                },
            }
            for item in faq_items
        ],
    }
    return json.dumps(data, ensure_ascii=False)


def howto_json(request, *, name, description, steps, total_time='PT1H'):
    """steps: list of dicts with name, text."""
    if not steps:
        return ''
    data = {
        '@context': 'https://schema.org',
        '@type': 'HowTo',
        'name': name,
        'description': description,
        'totalTime': total_time,
        'step': [
            {
                '@type': 'HowToStep',
                'position': i + 1,
                'name': step.get('name', f'Step {i + 1}'),
                'text': step.get('text', ''),
            }
            for i, step in enumerate(steps)
        ],
    }
    return json.dumps(data, ensure_ascii=False)


def article_json(request, *, title, description, url_path, date_published, date_modified=None):
    root = _public_root(request)
    data = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': title,
        'description': description,
        'url': request.build_absolute_uri(url_path),
        'datePublished': date_published.isoformat() if date_published else None,
        'author': {'@type': 'Organization', 'name': 'ExtraPaints'},
        'publisher': {
            '@type': 'Organization',
            'name': 'ExtraPaints',
            'logo': {'@type': 'ImageObject', 'url': f'{root}/static/images/extrapaints.jpg'},
        },
    }
    if date_modified:
        data['dateModified'] = date_modified.isoformat()
    return json.dumps({k: v for k, v in data.items() if v is not None}, ensure_ascii=False)
