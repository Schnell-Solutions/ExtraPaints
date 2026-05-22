from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings

from colors.models import Color


class Finish(models.Model):
    """Sheen level (e.g., Matte, Gloss)."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Surface(models.Model):
    """Surfaces like Wood, Concrete, Metal."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ApplicationMethod(models.Model):
    """Tools used for application (e.g., Brush, Roller)."""
    name = models.CharField(max_length=50, unique=True)
    icon = models.ImageField(
        upload_to="tools/icons/",
        blank=True,
        null=True,
        help_text="Upload a small icon (SVG or PNG) to display on the product page."
    )

    def __str__(self):
        return self.name


class Category(models.Model):
    """Main product category."""
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True)

    features_colors = models.BooleanField(
        default=True,
        help_text="Check if products in this category come in different colors."
    )
    features_sizes = models.BooleanField(
        default=True,
        help_text="Check if products in this category are sold in different sizes."
    )

    class Meta:
        verbose_name = "Product category"
        verbose_name_plural = "Product categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:160]
        super().save(*args, **kwargs)


class SubCategory(models.Model):
    """Optional subcategory."""
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="subcategories")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)

    class Meta:
        verbose_name_plural = "SubCategories"
        unique_together = ('category', 'name')
        ordering = ["name"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:160]
        super().save(*args, **kwargs)


class Size(models.Model):
    """Master table for available sizes."""
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SafetyDocument(models.Model):
    """Represents a safety or technical document."""
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
    language = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. English, French")
    version = models.CharField(max_length=50, blank=True, null=True)
    effective_date = models.DateField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    products = models.ManyToManyField(
        "Product",
        related_name="safety_documents",
        blank=True,
        help_text="Select all products this document applies to."
    )

    class Meta:
        ordering = ["doc_type", "title"]

    def __str__(self):
        return f"{self.title} ({self.get_doc_type_display()})"


class Product(models.Model):
    """Product model for all items."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField()

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="products"
    )
    main_image = models.ImageField(upload_to="products/main/", blank=True, null=True)

    finish = models.ForeignKey(
        Finish,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Sheen level (e.g. Matte, Gloss)."
    )
    coverage_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Coverage in square meters per liter (m2/L)."
    )
    drying_time = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. 'Touch dry in 2 hours'."
    )
    coats_required = models.PositiveIntegerField(blank=True, null=True)

    suitable_surfaces = models.ManyToManyField(Surface, blank=True, related_name="products")

    tools_needed = models.ManyToManyField(
        ApplicationMethod,
        blank=True,
        related_name="products",
        verbose_name="Tools Needed",
        help_text="Select tools required for application."
    )

    other_products_needed = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="required_by",
        verbose_name="Other Products Needed",
        help_text="Essential add-ons (e.g. Hardener, Thinner)."
    )

    related_products = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="related_to",
        help_text="Optional cross-sells (e.g. Similar paints)."
    )

    available_colors = models.ManyToManyField(Color, related_name="products", blank=True)
    available_sizes = models.ManyToManyField(Size, related_name="products", blank=True)

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
    """Stores user favorites."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="saved_products")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-saved_at"]
        verbose_name = "Saved Product"

    def __str__(self):
        return f"{self.user} saved {self.product}"