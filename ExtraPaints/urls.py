from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.sitemaps.views import sitemap
from home.views import robots_txt
from home.sitemaps import (
    StaticViewSitemap, ProductSitemap, ColorSitemap,
    PortfolioSitemap, IdeaSitemap, GuideSitemap,
)

admin.site.site_header = "ExtraPaints Administration"
admin.site.site_title = "ExtraPaints Admin"
admin.site.index_title = "Dashboard"

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'colors': ColorSitemap,
    'portfolio': PortfolioSitemap,
    'ideas': IdeaSitemap,
    'guides': GuideSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),

    # SEO PATHS (Robots & Sitemap)
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    #APPS
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('colors/', include('colors.urls')),
    path('products/', include('products.urls')),
    path('ideas/', include('ideas.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('guides/', include('guides.urls')),
    path('quote/', include('quote_request.urls')),
]

# Only registered when DEBUG is True (see settings.py). Required for /media/ uploads on runserver.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # App + assets/ files are served by django.contrib.staticfiles when DEBUG=True.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    