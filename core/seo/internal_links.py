from django.db.models import Q

from ideas.models import Idea
from portfolio.models import PortfolioProject


def related_for_product(product, *, color_limit=6, idea_limit=4, portfolio_limit=3, guide_limit=3):
    """Contextual internal links for product detail pages."""
    colors = list(product.available_colors.filter(is_active=True).order_by('name')[:color_limit])
    ideas = list(
        Idea.objects.filter(is_active=True, paint_colors__in=colors).distinct()[:idea_limit]
        if colors
        else Idea.objects.filter(is_active=True).order_by('-is_featured', '-created_at')[:idea_limit]
    )
    portfolio = list(
        PortfolioProject.objects.filter(is_active=True, products_used=product)
        .distinct()
        .order_by('-is_featured', '-created_at')[:portfolio_limit]
    )
    guides = []
    try:
        from guides.models import Guide

        guides = list(
            Guide.objects.filter(is_published=True)
            .filter(Q(related_products=product) | Q(is_featured=True))
            .distinct()
            .order_by('-is_featured', '-updated_at')[:guide_limit]
        )
    except Exception:
        pass
    return {
        'link_colors': colors,
        'link_ideas': ideas,
        'link_portfolio': portfolio,
        'link_guides': guides,
    }


def related_for_color(color, *, product_limit=6, idea_limit=4, portfolio_limit=3):
    from products.models import Product

    products = list(
        Product.objects.filter(is_active=True, available_colors=color)
        .select_related('category')[:product_limit]
    )
    ideas = list(
        Idea.objects.filter(is_active=True, paint_colors=color).distinct()[:idea_limit]
    )
    portfolio = list(
        PortfolioProject.objects.filter(is_active=True, colors_used=color)
        .distinct()[:portfolio_limit]
    )
    return {
        'link_products': products,
        'link_ideas': ideas,
        'link_portfolio': portfolio,
    }


def related_for_portfolio(project, *, product_limit=8):
    products = list(project.products_used.filter(is_active=True)[:product_limit])
    colors = list(project.colors_used.filter(is_active=True)[:8])
    return {'link_products': products, 'link_colors': colors}
