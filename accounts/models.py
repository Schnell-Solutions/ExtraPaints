from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    - Supports multiple roles (Admin, Staff, Customer, Distributor).
    - Stores additional customer-related info like full name, phone,
      and profile image.
    - Includes verification flags for email and phone to improve
      trust and security in the platform.
    """

    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        CUSTOMER = "CUSTOMER", "Customer"
        DISTRIBUTOR = "DISTRIBUTOR", "Distributor"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER
    )

    full_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to="users/", blank=True, null=True)

    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    def __str__(self):
        """
        Returns a human-readable identifier for the user.
        Falls back to email if username is not set.
        """
        return self.username or self.email


class Address(models.Model):
    """
    Reserved for a future distributor / delivery portal — not used in quote flow.

    ExtraPaints is quote-led, not checkout-led. This model is kept for admin and
    possible future B2B features; profile and quote views do not read it yet.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    label = models.CharField(max_length=50, default="Home")  # e.g. Home, Office
    street_address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)  # County/State
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default="Kenya")
    is_default = models.BooleanField(default=False)

    def __str__(self):
        """
        Returns a short string identifying the address.
        Useful for dropdowns in checkout (e.g., 'Home: Nairobi, Nairobi County').
        """
        return f"{self.label}: {self.city}, {self.region}"


class AccountDeletionRequest(models.Model):
    """Logged when a registered user requests account deletion (admin completes erasure)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending review'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deletion_requests',
    )
    email_snapshot = models.EmailField()
    username_snapshot = models.CharField(max_length=150)
    full_name_snapshot = models.CharField(max_length=200, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Account deletion request'
        verbose_name_plural = 'Account deletion requests'

    def __str__(self):
        return f'{self.email_snapshot} ({self.get_status_display()})'


class AuthOTP(models.Model):
    """One-time codes for email verification, password reset, and password change."""

    class Purpose(models.TextChoices):
        EMAIL_VERIFY = 'email_verify', 'Email verification'
        PASSWORD_RESET = 'password_reset', 'Password reset'
        PASSWORD_CHANGE = 'password_change', 'Password change'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auth_otps',
    )
    purpose = models.CharField(max_length=32, choices=Purpose.choices, db_index=True)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
        ]

    def __str__(self):
        return f'{self.user_id} — {self.purpose}'
