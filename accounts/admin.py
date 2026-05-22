from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import User, Address, AccountDeletionRequest, AuthOTP


# --- Address Inline (for displaying addresses within the User Admin) ---
class AddressInline(admin.TabularInline):
    """Future distributor portal — not used in quote flow."""
    model = Address
    extra = 0
    max_num = 5
    classes = ('collapse',)
    verbose_name = 'Future address (optional)'
    verbose_name_plural = 'Future addresses (quote flow does not use these yet)'
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


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'requested_at', 'email_snapshot', 'username_snapshot',
        'status', 'user', 'ip_address',
    )
    list_filter = ('status', 'requested_at')
    search_fields = ('email_snapshot', 'username_snapshot', 'full_name_snapshot')
    readonly_fields = (
        'user', 'email_snapshot', 'username_snapshot', 'full_name_snapshot',
        'reason', 'requested_at', 'ip_address',
    )
    actions = ['mark_completed', 'mark_cancelled']

    @admin.action(description='Mark selected as completed')
    def mark_completed(self, request, queryset):
        queryset.update(
            status=AccountDeletionRequest.Status.COMPLETED,
            processed_at=timezone.now(),
        )

    @admin.action(description='Mark selected as cancelled')
    def mark_cancelled(self, request, queryset):
        queryset.update(
            status=AccountDeletionRequest.Status.CANCELLED,
            processed_at=timezone.now(),
        )


@admin.register(AuthOTP)
class AuthOTPAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'purpose', 'expires_at', 'attempts', 'is_used')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('user', 'purpose', 'code_hash', 'created_at', 'expires_at', 'attempts', 'is_used')


# Address is reserved for a future distributor portal — manage via User inline only.