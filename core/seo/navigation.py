"""Primary site sections — used for sitelink-style SEO and on-page quick links."""

from django.urls import reverse

# Indexable pages only (no noindex routes). Descriptions match likely SERP sitelink copy.
SITE_PRIMARY_NAV = (
    {
        'url_name': 'product_list',
        'name': 'Paint products',
        'description': 'Browse interior, exterior, and specialty coatings for every project.',
    },
    {
        'url_name': 'color_list',
        'name': 'Color library',
        'description': 'Explore shades, hex codes, and shop products by color.',
    },
    {
        'url_name': 'contact',
        'name': 'Contact & quotes',
        'description': 'Request tailored quotations from our Nairobi and Eldoret teams.',
    },
    {
        'url_name': 'about',
        'name': 'About ExtraPaints',
        'description': 'Our story, leadership, and 3,000+ projects supplied across Kenya.',
    },
    {
        'url_name': 'guide_list',
        'name': 'Guides & resources',
        'description': 'Surface prep, finishes, and quotation tips for Kenyan projects.',
    },
    {
        'url_name': 'portfolio_list',
        'name': 'Project portfolio',
        'description': 'See residential, commercial, and industrial work with our products.',
    },
)


def primary_nav_links(request):
    """Absolute and relative URLs for primary navigation (templates + JSON-LD)."""
    links = []
    for item in SITE_PRIMARY_NAV:
        path = reverse(item['url_name'])
        links.append(
            {
                **item,
                'path': path,
                'url': request.build_absolute_uri(path),
            }
        )
    return links
