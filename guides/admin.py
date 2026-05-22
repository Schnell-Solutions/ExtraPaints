from django.contrib import admin

from .models import Guide


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('title', 'guide_type', 'is_published', 'is_featured', 'updated_at')
    list_filter = ('guide_type', 'is_published', 'is_featured')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('related_products', 'related_colors')
