from django.shortcuts import get_object_or_404, render



from core.seo.breadcrumbs import build_breadcrumbs

from core.seo.helpers import schema_json_ld_blocks

from core.seo.schema import (

    article_json,

    breadcrumb_list_json,

    faq_page_json,

    howto_json,

)

from .models import Guide





def guide_list(request):

    guides = Guide.objects.filter(is_published=True)

    breadcrumbs = build_breadcrumbs(request, ('Guides & Resources', None))

    context = {

        'guides': guides,

        'featured_guides': guides.filter(is_featured=True)[:3],

        'breadcrumbs': breadcrumbs,

        'schema_json_ld_blocks': schema_json_ld_blocks(

            breadcrumb_list_json(request, breadcrumbs),

        ),

    }

    return render(request, 'guides/guide_list.html', context)





def guide_detail(request, slug):

    guide = get_object_or_404(Guide, slug=slug, is_published=True)

    breadcrumbs = build_breadcrumbs(

        request,

        ('Guides & Resources', 'guide_list'),

        (guide.title, None),

    )

    schema_blocks = [breadcrumb_list_json(request, breadcrumbs)]



    if guide.guide_type == 'howto' and guide.howto_steps:

        schema_blocks.append(

            howto_json(

                request,

                name=guide.title,

                description=guide.excerpt,

                steps=guide.howto_steps,

                total_time=guide.howto_total_time or 'PT1H',

            )

        )

    elif guide.guide_type == 'faq' and guide.faq_items:

        schema_blocks.append(faq_page_json(guide.faq_items))

    else:

        schema_blocks.append(

            article_json(

                request,

                title=guide.title,

                description=guide.seo_description,

                url_path=guide.get_absolute_url(),

                date_published=guide.created_at,

                date_modified=guide.updated_at,

            )

        )

    if guide.faq_items and guide.guide_type != 'faq':

        schema_blocks.append(faq_page_json(guide.faq_items))



    context = {

        'guide': guide,

        'breadcrumbs': breadcrumbs,

        'faq_items': guide.faq_items,

        'schema_json_ld_blocks': schema_json_ld_blocks(*schema_blocks),

    }

    return render(request, 'guides/guide_detail.html', context)

