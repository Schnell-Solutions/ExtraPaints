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
    Stores multiple delivery addresses for each user.

    - Linked to a user via ForeignKey (One-to-Many relationship).
    - Allows customers to save different addresses (Home, Office, etc.).
    - Supports marking one address as default for faster checkout.
    - Keeps delivery info separate from User to avoid data duplication.
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
