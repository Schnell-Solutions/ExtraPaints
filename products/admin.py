from django.contrib import admin
from .models import Category, SubCategory, Size, Product, SafetyDocument, SavedProducts


# ---------- INLINE SETUP ----------
class SafetyDocumentInline(admin.TabularInline):
    """Inline to quickly view/edit documents attached to a product."""
    model = SafetyDocument.products.through
    extra = 0
    verbose_name = "Safety Document"
    verbose_name_plural = "Linked Safety Documents"
    classes = ("collapse",)
    autocomplete_fields = ("safetydocument",)


class SubCategoryInline(admin.TabularInline):
    """Inline to add subcategories directly from the Main Category page."""
    model = SubCategory
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


# ---------- CATEGORY ADMIN (Main Category) ----------
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
    autocomplete_fields = ("category",) # Useful if you have many main categories


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
        "subcategory", # Added subcategory to list view
        "is_active",
        "created_at",
    )
    list_filter = (
        "category",
        "subcategory", # Added subcategory filter
        "is_active",
        "created_at",
    )
    search_fields = ("name", "description", "category__name", "subcategory__name")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at",)
    filter_horizontal = ("available_colors", "available_sizes")
    ordering = ("-created_at",)
    inlines = [SafetyDocumentInline]
    autocomplete_fields = ("category", "subcategory") # Improves performance with many categories

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