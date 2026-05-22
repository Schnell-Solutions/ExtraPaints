from django.contrib import admin
from .models import (
    ColorCollection,
    RoomType,
    ColorImage,
    Color,
    SavedColor,
)


# --- ColorCollection Admin ---
@admin.register(ColorCollection)
class ColorCollectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "description")
    search_fields = ("name", "description")
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
        if obj.image:
            return f'<img src="{obj.image.url}" width="80" style="border-radius:4px;" />'
        return "—"

    image_preview.allow_tags = True
    image_preview.short_description = "Preview"


# --- Color Admin ---
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
        "color_preview",
    )
    list_filter = (
        "collection",
        "undertone",
        "opacity_strength",
        "is_active",
    )
    search_fields = ("name", "code", "description", "collection__name")

    readonly_fields = ("created_at", "updated_at", "slug", "color_preview")

    autocomplete_fields = ("collection",)
    filter_horizontal = (
        "recommended_rooms",
        "inspiration_images",
    )
    ordering = ("name",)

    fieldsets = (
        ("Basic Info", {
            "fields": ("name", "code", "slug", "description", "is_active")
        }),
        ("Visual Attributes", {
            "fields": (
                "hex_code",
                "rgb_value",
                "cmyk_value",
                "undertone",
                "lrv",
                "opacity_strength",
                "color_preview",
            )
        }),
        ("Associations", {
            "fields": (
                "collection",
                "recommended_rooms",
                "inspiration_images",
            )
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
    search_fields = ("user__username", "color__name", "color__code")
    autocomplete_fields = ("user", "color")
    readonly_fields = ("saved_at",)
    ordering = ("-saved_at",)