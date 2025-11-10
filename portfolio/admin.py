from django.contrib import admin
from .models import PortfolioProject, PortfolioImage


# ---------- INLINE FOR GALLERY IMAGES ----------
class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 1
    fields = ("image", "caption", "alt_text", "display_order",)
    readonly_fields = ()
    ordering = ("display_order",)
    classes = ("collapse",)  # collapsible inline for cleaner view
    show_change_link = True


# ---------- MAIN PROJECT ADMIN ----------
@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project_type",
        "location",
        "completion_date",
        "is_featured",
        "is_active",
        "created_at",
    )
    list_filter = (
        "project_type",
        "is_featured",
        "is_active",
        "completion_date",
        "created_at",
    )
    search_fields = ("title", "location", "client_name", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at",)
    inlines = [PortfolioImageInline]
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "title",
                "slug",
                "project_type",
                "description",
                "featured_image",
            )
        }),
        ("Client & Location", {
            "fields": (
                "client_name",
                "location",
                "completion_date",
            ),
            "classes": ("collapse",),
        }),
        ("Associations", {
            "fields": (
                "products_used",
                "colors_used",
            ),
            "classes": ("collapse",),
        }),
        ("Visibility & Metadata", {
            "fields": (
                "is_featured",
                "is_active",
                "created_at",
                "updated_at",
            ),
        }),
    )


# ---------- IMAGE ADMIN ----------
@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "caption",
        "display_order",
    )
    list_filter = ("project",)
    search_fields = ("caption", "alt_text", "project__title")
    ordering = ("project", "display_order")
