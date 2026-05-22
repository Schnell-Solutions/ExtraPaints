from django.db import migrations


def seed_guides(apps, schema_editor):
    Guide = apps.get_model('guides', 'Guide')
    if Guide.objects.exists():
        return

    guides = [
        {
            'title': 'Best exterior paint for Nairobi weather',
            'slug': 'best-exterior-paint-nairobi-weather',
            'guide_type': 'article',
            'excerpt': (
                'How to choose exterior coatings that stand up to sun, rain, and dust '
                'in Nairobi and wider Kenya.'
            ),
            'meta_description': (
                'Guide to exterior paint for Nairobi climate — UV resistance, primers, '
                'and quotation tips from ExtraPaints Kenya.'
            ),
            'body': (
                '<p>Nairobi\'s climate combines strong UV, seasonal rain, and dust — exterior '
                'systems must flex and adhere long term.</p>'
                '<h2>Choose the right system</h2>'
                '<p>Start with a compatible primer, then apply UV-resistant exterior emulsion '
                'or elastomeric topcoats for exposed walls.</p>'
                '<h2>Application timing</h2>'
                '<p>Paint during dry weather and allow surfaces to cure per technical data sheets.</p>'
                '<h2>Get a project quote</h2>'
                '<p>Build your quote list on our website or contact sales for bulk contractor pricing.</p>'
            ),
            'faq_items': [
                {
                    'question': 'How often should exterior walls be repainted in Nairobi?',
                    'answer': 'Typically every 5–8 years depending on exposure, quality of preparation, and product system.',
                },
                {
                    'question': 'Can ExtraPaints recommend a full exterior system?',
                    'answer': 'Yes — share substrate photos and square metres; our team will propose primer and topcoat options.',
                },
            ],
            'is_featured': True,
        },
        {
            'title': 'How to prepare walls before painting',
            'slug': 'how-to-prepare-walls-before-painting',
            'guide_type': 'howto',
            'excerpt': 'Surface preparation steps for interior and exterior painting projects in Kenya.',
            'meta_description': 'Step-by-step wall preparation for painting — cleaning, repairs, priming — ExtraPaints Kenya.',
            'body': '<p>Good preparation prevents peeling and uneven colour. Follow these steps before any topcoat.</p>',
            'howto_steps': [
                {'name': 'Inspect and repair', 'text': 'Fill cracks, remove loose plaster, and fix damp sources before painting.'},
                {'name': 'Clean the surface', 'text': 'Wash dust, grease, and mildew; allow walls to dry completely.'},
                {'name': 'Sand and dust off', 'text': 'Lightly sand glossy areas; vacuum or wipe dust.'},
                {'name': 'Prime', 'text': 'Apply the primer recommended for your substrate and topcoat system.'},
                {'name': 'Apply finish coats', 'text': 'Apply two uniform finishing coats, respecting drying times.'},
            ],
            'howto_total_time': 'PT4H',
            'is_featured': True,
        },
        {
            'title': 'Interior vs exterior paint — what is the difference?',
            'slug': 'interior-vs-exterior-paint',
            'guide_type': 'faq',
            'excerpt': 'Key differences between interior and exterior paint formulations for Kenyan projects.',
            'meta_description': 'Interior vs exterior paint explained for contractors and homeowners in Kenya.',
            'body': '<p>Using the wrong paint type leads to early failure. Here are the essentials.</p>',
            'faq_items': [
                {
                    'question': 'Can I use interior paint outside?',
                    'answer': 'No. Exterior paints contain additives for UV and weather resistance that interior formulas lack.',
                },
                {
                    'question': 'Is exterior paint harder to clean?',
                    'answer': 'Exterior coatings prioritize weatherability; interior paints often offer better stain resistance for busy rooms.',
                },
                {
                    'question': 'Which paint is best for bathrooms?',
                    'answer': 'Use a moisture-resistant interior system with appropriate primer for your substrate.',
                },
            ],
            'is_featured': False,
        },
        {
            'title': 'Eco-friendly paints in Kenya',
            'slug': 'eco-friendly-paints-kenya',
            'guide_type': 'article',
            'excerpt': 'Low-VOC and environmentally conscious paint options for healthier indoor spaces.',
            'meta_description': 'Eco-friendly and low-VOC paint options in Kenya — ExtraPaints professional supply.',
            'body': (
                '<p>Low-VOC interior ranges reduce odour and improve occupant comfort during and after painting.</p>'
                '<p>Ask our sales team which eco-conscious products fit your commercial or residential specification.</p>'
            ),
            'faq_items': [
                {
                    'question': 'Are eco-friendly paints durable?',
                    'answer': 'Modern low-VOC systems offer strong durability when paired with correct primers and application.',
                },
            ],
            'is_featured': True,
        },
    ]

    for data in guides:
        Guide.objects.create(**data)


def unseed(apps, schema_editor):
    Guide = apps.get_model('guides', 'Guide')
    Guide.objects.filter(
        slug__in=[
            'best-exterior-paint-nairobi-weather',
            'how-to-prepare-walls-before-painting',
            'interior-vs-exterior-paint',
            'eco-friendly-paints-kenya',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('guides', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_guides, unseed),
    ]
