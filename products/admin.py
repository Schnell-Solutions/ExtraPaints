from django.contrib import admin
from products.models import Category, Product, Size, SafetyDocument, Color


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    filter_horizontal = ('available_colors', 'available_sizes')

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'description', 'main_image', 'is_active')
        }),
        ('Variants', {
            'fields': ('available_colors', 'available_sizes')
        }),
    )


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(SafetyDocument)
class SafetyDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'is_active', 'uploaded_at')
    list_filter = ('doc_type', 'is_active', 'language')
    search_fields = ('title', 'description')

    # Also good for M2M fields on this model
    filter_horizontal = ('products',)