from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from core.pagination import paginate_queryset
from core.seo.breadcrumbs import build_breadcrumbs
from core.seo.helpers import schema_json_ld_blocks
from core.seo.internal_links import related_for_portfolio
from core.seo.schema import breadcrumb_list_json
from .models import PortfolioProject


def portfolio_list(request):
    projects_list = PortfolioProject.objects.filter(is_active=True).order_by('-is_featured', '-created_at')

    project_types = projects_list.order_by('project_type').values_list('project_type', flat=True).distinct()

    selected_type = request.GET.get('type')
    if selected_type:
        projects_list = projects_list.filter(project_type=selected_type)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        page_obj, _ = paginate_queryset(projects_list, request)
        payload = []
        for project in page_obj:
            img = project.get_display_image
            try:
                from core.images import thumbnail_for_image_url
                img = thumbnail_for_image_url(img, width=400) if img else img
            except Exception:
                pass
            payload.append({
                'title': project.title,
                'url': project.get_absolute_url(),
                'image_url': img,
                'project_type': project.get_project_type_display(),
                'location': project.location or '',
            })
        return JsonResponse({
            'projects': payload,
            'page': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        })

    page_obj, paginator = paginate_queryset(projects_list, request)
    breadcrumbs = build_breadcrumbs(request, ('Portfolio', None))
    query_string = f'type={selected_type}' if selected_type else ''

    return render(request, "portfolio/portfolio_list.html", {
        "projects": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "query_string": query_string,
        "project_types": project_types,
        "selected_type": selected_type,
        "breadcrumbs": breadcrumbs,
        "schema_json_ld_blocks": schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
        ),
    })


def portfolio_detail(request, slug):
    project = get_object_or_404(
        PortfolioProject.objects.prefetch_related(
            'gallery_images',
            'products_used__category',
            'products_used__available_sizes',
            'colors_used',
        ),
        slug=slug,
        is_active=True,
    )

    breadcrumbs = build_breadcrumbs(
        request,
        ('Portfolio', 'portfolio_list'),
        (project.title, None),
    )
    return render(request, "portfolio/portfolio_detail.html", {
        "project": project,
        "breadcrumbs": breadcrumbs,
        "schema_json_ld_blocks": schema_json_ld_blocks(
            breadcrumb_list_json(request, breadcrumbs),
        ),
        **related_for_portfolio(project),
    })
