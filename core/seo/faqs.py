"""Reusable FAQ content for category pages and product detail (SEO + conversion)."""

PRODUCT_GENERAL_FAQS = [
    {
        'question': 'How do I get a price for this product?',
        'answer': (
            'Add products to your quote list and submit your details. Our sales team '
            'prepares a tailored quotation for your project — we do not display checkout prices online.'
        ),
    },
    {
        'question': 'Do you supply contractors and distributors in Kenya?',
        'answer': (
            'Yes. ExtraPaints works with contractors, painters, developers, and distributors '
            'across Nairobi, Eldoret, and wider Kenya with project-based supply and quotations.'
        ),
    },
    {
        'question': 'Can I request technical data sheets (SDS/TDS)?',
        'answer': (
            'Yes. Product pages include safety and technical documents where available. '
            'Contact our sales team for additional specifications.'
        ),
    },
]

CATEGORY_FAQS = {
    'interior': [
        {
            'question': 'What interior paint works best for Nairobi homes?',
            'answer': (
                'Washable matt and silk finishes are popular for living areas; '
                'moisture-resistant systems suit kitchens and bathrooms. Our team can recommend '
                'a system based on substrate and traffic.'
            ),
        },
        {
            'question': 'How many coats are typical for interior walls?',
            'answer': (
                'Most interior systems use two finishing coats over a suitable primer. '
                'Deep colours may need additional coats — confirm quantities on your quote.'
            ),
        },
    ],
    'exterior': [
        {
            'question': 'Which exterior paint suits Kenya’s sun and rain?',
            'answer': (
                'UV-resistant exterior emulsions and elastomeric coatings help withstand '
                'Nairobi weather cycles. We recommend compatible primers for long-term adhesion.'
            ),
        },
        {
            'question': 'When is the best time to paint exterior walls in Kenya?',
            'answer': (
                'Dry seasons are ideal. Avoid painting during heavy rain; '
                'allow surfaces to dry and follow product TDS drying times.'
            ),
        },
    ],
    'commercial': [
        {
            'question': 'Do you supply commercial and industrial coatings?',
            'answer': (
                'Yes — floor, protective, and high-traffic coatings for retail, warehouses, '
                'and facilities. Request a site-specific quotation from our sales team.'
            ),
        },
    ],
}


def faqs_for_product(product):
    """Merge general FAQs with category-specific entries."""
    items = list(PRODUCT_GENERAL_FAQS)
    slug = (product.category.slug or '').lower()
    for key, extra in CATEGORY_FAQS.items():
        if key in slug:
            items.extend(extra)
            break
    return items[:6]


def faqs_for_category_slug(slug):
    slug = (slug or '').lower()
    items = list(PRODUCT_GENERAL_FAQS)[:2]
    for key, extra in CATEGORY_FAQS.items():
        if key in slug:
            items.extend(extra)
            break
    return items[:6]
