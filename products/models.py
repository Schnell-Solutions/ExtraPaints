from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings

from colors.models import Color


class Category(models.Model):
    """Category representing a paint product category (e.g., Exterior, Interior, Primer)."""
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=160, unique=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:160]
        super().save(*args, **kwargs)


class Size(models.Model):
    """Master table for available sizes (e.g., 1L, 5L, 20L)."""
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Size"
        verbose_name_plural = "Sizes"
        ordering = ["name"]  # Consider ordering by a value field later if 1L, 5L, 10L isn't alphabetical

    def __str__(self):
        return self.name


class SafetyDocument(models.Model):
    """Represents a safety, technical, or compliance document related to one or more paint products."""

    SAFETY_DOC_TYPES = [
        ("SDS", "Safety Data Sheet (SDS)"),
        ("TDS", "Technical Data Sheet (TDS)"),
        ("CERT", "Certification / Compliance Document"),
        ("GUIDE", "Application Guide / Brochure"),
        ("OTHER", "Other"),
    ]

    doc_type = models.CharField(max_length=20, choices=SAFETY_DOC_TYPES)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="products/safety_docs/")
    language = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. English, French, Swahili")
    version = models.CharField(max_length=50, blank=True, null=True, help_text="Document version or revision code")
    effective_date = models.DateField(blank=True, null=True, help_text="Date the document became valid")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    products = models.ManyToManyField(
        "Product",
        related_name="safety_documents",
        blank=True,
        help_text="Products this document applies to"
    )

    class Meta:
        verbose_name = "Safety Document"
        verbose_name_plural = "Safety Documents"
        ordering = ["doc_type", "title"]

    def __str__(self):
        return f"{self.title} ({self.get_doc_type_display()})"


class Product(models.Model):
    """Product model for paint products."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey("Category", on_delete=models.PROTECT, related_name="products")

    # Main image for the product (e.g., a room shot, or lifestyle image)
    main_image = models.ImageField(upload_to="products/main/", blank=True, null=True)

    # UPDATED: List of available colors for this product.
    available_colors = models.ManyToManyField(
        Color,
        related_name="products",
        blank=True,
        help_text="Colors this product is available in."
    )

    # UPDATED: List of available sizes for this product.
    available_sizes = models.ManyToManyField(
        "Size",
        related_name="products",
        blank=True,
        help_text="Sizes this product is sold in."
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.slug])


class SavedProducts(models.Model):
    """
    Stores products that users have saved (favorites/bookmarks).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_products"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="saved_products"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-saved_at"]
        verbose_name = "Saved Product"
        verbose_name_plural = "Saved Products"

    def __str__(self):
        return f"{self.user} saved {self.product}"
