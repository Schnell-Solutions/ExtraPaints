from django.contrib.sitemaps import Sitemap
from django.urls import reverse

# Import your models
from products.models import Product
from colors.models import Color
from ideas.models import Idea
from portfolio.models import PortfolioProject

class StaticViewSitemap(Sitemap):
    """
    Maps static pages like Home, About, Contact.
    Priority tiers help crawlers discover sitelink candidate pages.
    """
    changefreq = 'monthly'

    _PRIORITY = {
        'home': 1.0,
        'product_list': 0.95,
        'color_list': 0.9,
        'contact': 0.85,
        'about': 0.85,
        'guide_list': 0.8,
        'portfolio_list': 0.75,
        'idea_list': 0.75,
        'privacy_policy': 0.3,
        'terms_conditions': 0.3,
    }

    def items(self):
        return [
            'home', 'product_list', 'color_list', 'contact', 'about',
            'guide_list', 'portfolio_list', 'idea_list',
            'privacy_policy', 'terms_conditions',
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self._PRIORITY.get(item, 0.5)

class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

class ColorSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Color.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

class PortfolioSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return PortfolioProject.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

class IdeaSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Assumes Idea has is_active and updated_at (standard practice)
        return Idea.objects.filter(is_active=True)

    def lastmod(self, obj):
        # If Idea doesn't have updated_at, change this to obj.created_at
        return obj.updated_at or obj.created_at


class GuideSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.75

    def items(self):
        from guides.models import Guide
        return Guide.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at