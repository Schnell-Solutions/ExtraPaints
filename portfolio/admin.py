from django.contrib import admin

from portfolio.models import PortfolioProject, PortfolioImage

admin.site.register(PortfolioProject)
admin.site.register(PortfolioImage)
