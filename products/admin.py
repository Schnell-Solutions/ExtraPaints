from django.contrib import admin
from .models import (
    Category, SubCategory, Size, Product, SafetyDocument, SavedProducts,
    Finish, Surface, ApplicationMethod
)


# ---------- INLINE SETUP ----------
class SafetyDocumentInline(admin.TabularInline):
    model = SafetyDocument.products.through
    extra = 0
    verbose_name = "Safety Document"
    verbose_name_plural = "Linked Safety Documents"
    classes = ("collapse",)
    autocomplete_fields = ("safetydocument",)


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


# ---------- HELPER ADMINS ----------
@admin.register(Finish)
class FinishAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Surface)
class SurfaceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ApplicationMethod)
class ApplicationMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")
    search_fields = ("name",)


# ---------- CATEGORY ADMIN ----------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "features_colors", "features_sizes")
    list_filter = ("features_colors", "features_sizes")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    inlines = [SubCategoryInline]
    fieldsets = (
        (None, {
            "fields": ("name", "slug")
        }),
        ("Feature Flags", {
            "fields": ("features_colors", "features_sizes"),
            "description": "Control which features are active for products in this category."
        }),
    )


# ---------- SUBCATEGORY ADMIN ----------
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug")
    list_filter = ("category",)
    search_fields = ("name", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("category", "name")
    autocomplete_fields = ("category",)


# ---------- SIZE ADMIN ----------
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


# ---------- PRODUCT ADMIN ----------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "subcategory",
        "finish",
        "is_active",
        "created_at",
    )
    list_filter = (
        "category",
        "subcategory",
        "finish",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "description", "category__name", "subcategory__name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at",)

    # Use filter_horizontal for better UX on ManyToMany fields
    filter_horizontal = (
        "available_colors",
        "available_sizes",
        "suitable_surfaces",
        "tools_needed",
        "other_products_needed",
        "related_products"
    )

    ordering = ("-created_at",)
    inlines = [SafetyDocumentInline]
    autocomplete_fields = ("category", "subcategory", "finish")

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "name",
                "slug",
                "description",
                "main_image",
            )
        }),
        ("Categorization", {
            "fields": (
                "category",
                "subcategory",
            )
        }),
        ("Technical Specifications", {
            "fields": (
                "finish",
                "coverage_rate",
                "drying_time",
                "coats_required",
            )
        }),
        ("Application & Usage", {
            "fields": (
                "suitable_surfaces",
                "tools_needed",
            ),
            "classes": ("collapse",)
        }),
        ("Cross-Selling & Relations", {
            "fields": (
                "other_products_needed",
                "related_products",
            ),
            "classes": ("collapse",)
        }),
        ("Options & Availability", {
            "fields": (
                "available_colors",
                "available_sizes",
                "is_active",
            ),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


# ---------- SAFETY DOCUMENT ADMIN ----------
@admin.register(SafetyDocument)
class SafetyDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "doc_type",
        "language",
        "version",
        "effective_date",
        "is_active",
        "uploaded_at",
    )
    list_filter = (
        "doc_type",
        "language",
        "is_active",
        "effective_date",
        "uploaded_at",
    )
    search_fields = ("title", "version", "language", "products__name")
    filter_horizontal = ("products",)
    ordering = ("doc_type", "title")
    fieldsets = (
        ("Document Info", {
            "fields": (
                "doc_type",
                "title",
                "file",
                "language",
                "version",
                "effective_date",
            )
        }),
        ("Associations", {
            "fields": ("products",),
            "classes": ("collapse",)
        }),
        ("Status", {
            "fields": ("is_active",),
        }),
    )


# ---------- SAVED PRODUCTS ADMIN ----------
@admin.register(SavedProducts)
class SavedProductsAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "saved_at")
    list_filter = ("saved_at",)
    search_fields = ("user__username", "product__name")
    readonly_fields = ("saved_at",)
    ordering = ("-saved_at",)