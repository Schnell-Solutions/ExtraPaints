from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


# --- Address Inline (for displaying addresses within the User Admin) ---
class AddressInline(admin.TabularInline):
    """
    Displays the user's saved addresses directly within the User Admin page.
    """
    model = Address
    extra = 1  # Number of empty forms to display
    fields = (
        "label",
        "street_address",
        "city",
        "region",
        "postal_code",
        "country",
        "is_default"
    )


# --- Custom User Admin ---
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.
    Extends Django's BaseUserAdmin for standard security fields.
    """
    inlines = [AddressInline]

    # Fields for the main list view
    list_display = (
        "username",
        "email",
        "full_name",
        "role",
        "is_email_verified",
        "is_phone_verified",
        "is_staff",
    )

    # Filters for the list view sidebar
    list_filter = (
        "role",
        "is_email_verified",
        "is_phone_verified",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    )

    # Fields that can be searched
    search_fields = ("username", "email", "full_name", "phone")

    # Read-only fields (set automatically by Django/your code)
    readonly_fields = ("last_login", "date_joined")

    # Custom fieldsets, replacing the default AbstractUser fieldsets
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal Info",
            {"fields": ("full_name", "email", "phone", "profile_image")},
        ),
        (
            "Permissions & Status",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Verification Status",
            {"fields": ("is_email_verified", "is_phone_verified")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


# --- Address Admin ---
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Address model.
    """
    list_display = (
        "user",
        "label",
        "city",
        "region",
        "is_default",
    )
    list_filter = ("country", "region", "is_default")

    # Use autocomplete for the user ForeignKey for better performance
    # when you have many users.
    autocomplete_fields = ("user",)

    search_fields = (
        "user__username",
        "user__email",
        "label",
        "street_address",
        "city"
    )
    ordering = ("user__username", "-is_default", "label")