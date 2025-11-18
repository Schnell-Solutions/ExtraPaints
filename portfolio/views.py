from django.shortcuts import render, get_object_or_404
from .models import PortfolioProject


def portfolio_list(request):
    """
    Displays a list of all active portfolio projects, with filtering
    by project type.
    """
    projects_list = PortfolioProject.objects.filter(is_active=True)

    # Get all unique, non-empty project types from the active projects
    project_types = projects_list.order_by('project_type').values_list('project_type', flat=True).distinct()

    # --- Filter by Project Type ---
    selected_type = request.GET.get('type')
    if selected_type:
        projects_list = projects_list.filter(project_type=selected_type)

    return render(request, "portfolio/portfolio_list.html", {
        "projects": projects_list,
        "project_types": project_types,
        "selected_type": selected_type,
    })


def portfolio_detail(request, slug):
    """
    Displays the details for a single portfolio project, including
    gallery images, products used, and colors used.
    """
    project = get_object_or_404(
        PortfolioProject.objects.prefetch_related(
            'gallery_images',
            'products_used__category',  # Prefetch product category
            'products_used__available_sizes',  # Prefetch product sizes if needed
            'colors_used'
        ),
        slug=slug,
        is_active=True
    )

    return render(request, "portfolio/portfolio_detail.html", {
        "project": project
    })
