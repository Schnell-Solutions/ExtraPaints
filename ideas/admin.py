from django.contrib import admin
from .models import Category, Tag, Idea, IdeaImage, SavedIdea


# --- Inline for Idea Images ---
class IdeaImageInline(admin.TabularInline):
    model = IdeaImage
    extra = 1
    fields = ("image", "caption", "display_order", "image_preview")
    readonly_fields = ("image_preview",)
    ordering = ("display_order",)

    def image_preview(self, obj):
        if obj.image:
            # NOTE: Consider marking safe in a template if allowing HTML is preferred
            return f'<img src="{obj.image.url}" width="80" style="border-radius:6px;" />'
        return "—"

    image_preview.allow_tags = True
    image_preview.short_description = "Preview"


# --- Category Admin ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    fieldsets = (
        ("Category Info", {"fields": ("name", "description")}),
        ("Slug", {"fields": ("slug",)}),
    )


# --- Tag Admin ---
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


# --- Idea Admin (FIXED) ---
@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "created_by",
        "is_featured",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_featured",
        "is_active",
        "category",
        "tags",
        "paint_colors",
        "created_at",
    )
    search_fields = ("title", "description", "category__name", "tags__name")

    # 'slug' is here, making it display-only (not editable)
    readonly_fields = ("created_at", "updated_at", "slug", "image_preview")

    # REMOVED: prepopulated_fields = {"slug": ("title",)}
    # This line conflicted with 'slug' being in readonly_fields, causing the 500 error.

    inlines = [IdeaImageInline]
    autocomplete_fields = ("category", "created_by", "paint_colors", "tags")
    filter_horizontal = ("tags", "paint_colors")
    ordering = ("-created_at",)
    list_per_page = 25

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "title",
                "slug",  # Displayed because it's in readonly_fields
                "description",
                "category",
                "tags",
                "created_by",
                "mood",
            )
        }),
        ("Paint & Visuals", {
            "fields": (
                "paint_colors",
                "main_image",
                "image_preview",
            )
        }),
        ("Status & Options", {
            "fields": ("is_featured", "is_active"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def image_preview(self, obj):
        """Show a small preview of the main image."""
        if obj.main_image:
            return f'<img src="{obj.main_image.url}" width="80" style="border-radius:6px;" />'
        return "—"

    image_preview.allow_tags = True
    image_preview.short_description = "Main Image Preview"


# --- Saved Ideas Admin ---
@admin.register(SavedIdea)
class SavedIdeaAdmin(admin.ModelAdmin):
    list_display = ("user", "idea", "saved_at")
    list_filter = ("saved_at",)
    search_fields = ("user__username", "idea__title")
    autocomplete_fields = ("user", "idea")
    readonly_fields = ("saved_at",)
    ordering = ("-saved_at",)
    list_per_page = 25