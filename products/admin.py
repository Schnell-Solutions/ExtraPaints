from django.contrib import admin
from .models import Category, Size, Product, SafetyDocument, SavedProducts


# ---------- INLINE SETUP ----------
class SafetyDocumentInline(admin.TabularInline):
    """Inline to quickly view/edit documents attached to a product."""
    model = SafetyDocument.products.through
    extra = 0
    verbose_name = "Safety Document"
    verbose_name_plural = "Linked Safety Documents"
    classes = ("collapse",)
    autocomplete_fields = ("safetydocument",)


# ---------- CATEGORY ADMIN ----------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    fieldsets = (
        (None, {
            "fields": ("name", "slug", "description")
        }),
    )


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
        "is_active",
        "created_at",
    )
    list_filter = (
        "category",
        "available_sizes",
        "available_colors",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "description", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at",)
    filter_horizontal = ("available_colors", "available_sizes")
    ordering = ("-created_at",)
    inlines = [SafetyDocumentInline]

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "name",
                "slug",
                "description",
                "category",
                "main_image",
            )
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
