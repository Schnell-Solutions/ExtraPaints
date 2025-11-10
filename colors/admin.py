from django.contrib import admin
from .models import (
    ColorCollection,
    Finish,
    Surface,
    RoomType,
    ColorImage,
    Color,
    SavedColor,
)


# --- ColorCollection Admin ---
@admin.register(ColorCollection)
class ColorCollectionAdmin(admin.ModelAdmin):
    # OK: 'slug' is not in readonly_fields, so prepopulation works correctly.
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "description")
    search_fields = ("name", "description")
    ordering = ("name",)
    fieldsets = (
        ("Collection Info", {"fields": ("name", "description")}),
        ("SEO / Slug", {"fields": ("slug",)}),
    )


# --- Finish Admin ---
@admin.register(Finish)
class FinishAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    ordering = ("name",)


# --- Surface Admin ---
@admin.register(Surface)
class SurfaceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


# --- RoomType Admin ---
@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


# --- ColorImage Admin ---
@admin.register(ColorImage)
class ColorImageAdmin(admin.ModelAdmin):
    list_display = ("caption", "image_preview")
    search_fields = ("caption",)
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        # NOTE: Allow_tags usage is discouraged in modern Django versions,
        # but this is fine for older versions or if the template filter is registered.
        if obj.image:
            return f'<img src="{obj.image.url}" width="80" style="border-radius:4px;" />'
        return "—"

    image_preview.allow_tags = True
    image_preview.short_description = "Preview"


# --- Color Admin (Primary Fix Applied Here) ---
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "collection",
        "undertone",
        "opacity_strength",
        "is_active",
        "created_at",
        "color_preview",  # <--- Added color_preview to list_display for quick view
    )
    list_filter = (
        "collection",
        "undertone",
        "opacity_strength",
        "is_active",
        "available_finishes",
    )
    search_fields = ("name", "code", "description", "collection__name")

    # FIX: Removed 'prepopulated_fields' entirely because 'slug' is in 'readonly_fields'.
    # The slug generation logic is safely handled in the Color model's save() method.
    readonly_fields = ("created_at", "updated_at", "slug", "color_preview")

    autocomplete_fields = ("collection",)
    filter_horizontal = (
        "available_finishes",
        "recommended_surfaces",
        "recommended_rooms",
        "inspiration_images",
    )
    ordering = ("name",)

    fieldsets = (
        ("Basic Info", {
            # Note: 'slug' is here because it's in readonly_fields, allowing it to be displayed.
            "fields": ("name", "code", "slug", "description", "is_active")
        }),
        ("Color Attributes", {
            "fields": (
                "hex_code",
                "rgb_value",
                "cmyk_value",
                "undertone",
                "lrv",
                "opacity_strength",
                "voc_level",
                "color_preview",
            )
        }),
        ("Associations", {
            "fields": (
                "collection",
                "available_finishes",
                "recommended_surfaces",
                "recommended_rooms",
                "inspiration_images",
            )
        }),
        ("Technical Details", {
            "fields": ("coverage_per_liter", "drying_time_hours")
        }),
        ("Images", {
            "fields": ("main_image",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def color_preview(self, obj):
        """Show color swatch in admin."""
        if obj.hex_code:
            return f'<div style="width:40px; height:20px; background:{obj.hex_code}; border:1px solid #ccc;"></div>'
        return "—"

    color_preview.allow_tags = True
    color_preview.short_description = "Preview"


# --- SavedColor Admin ---
@admin.register(SavedColor)
class SavedColorAdmin(admin.ModelAdmin):
    list_display = ("user", "color", "saved_at")
    list_filter = ("saved_at",)
    # OK: Using autocomplete_fields for ForeignKeys is a good practice.
    search_fields = ("user__username", "color__name", "color__code")
    autocomplete_fields = ("user", "color")
    readonly_fields = ("saved_at",)
    ordering = ("-saved_at",)