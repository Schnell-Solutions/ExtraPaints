from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# SEO IMPORTS
from django.contrib.sitemaps.views import sitemap
from django.views.generic.base import TemplateView
from home.sitemaps import (
    StaticViewSitemap, ProductSitemap, ColorSitemap,
    PortfolioSitemap, IdeaSitemap
)

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'colors': ColorSitemap,
    'portfolio': PortfolioSitemap,
    'ideas': IdeaSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),

    # SEO PATHS (Robots & Sitemap)
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    #APPS
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('colors/', include('colors.urls')),
    path('products/', include('products.urls')),
    path('ideas/', include('ideas.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('quote/', include('quote_request.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)