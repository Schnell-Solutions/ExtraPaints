from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings


class ColorCollection(models.Model):
    """Group of colors, e.g., Designer Series, Coastal Collection."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:120]
        super().save(*args, **kwargs)


class Finish(models.Model):
    """Paint finishes like Matte, Satin, Gloss."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Surface(models.Model):
    """Surface recommendations (walls, wood, metal, etc.)."""
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RoomType(models.Model):
    """Room or area recommendations."""
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ColorImage(models.Model):
    """Images showing color inspiration or real-life usage."""
    image = models.ImageField(upload_to="colors/inspirations/")
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.caption or "Color Inspiration Image"


class Color(models.Model):
    """Master table for available colors with detailed attributes."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, help_text="e.g., OB-202")
    slug = models.SlugField(max_length=150, unique=True, blank=True)

    hex_code = models.CharField(max_length=7, blank=True, null=True, help_text="Optional HEX code for display")
    rgb_value = models.CharField(max_length=20, blank=True, null=True)
    cmyk_value = models.CharField(max_length=20, blank=True, null=True)

    undertone = models.CharField(
        max_length=50,
        choices=[("warm", "Warm"), ("cool", "Cool"), ("neutral", "Neutral")],
        blank=True, null=True
    )
    lrv = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Light Reflectance Value")
    opacity_strength = models.CharField(
        max_length=50,
        choices=[("weak", "Weak"), ("medium", "Medium"), ("strong", "Strong")],
        blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)

    collection = models.ForeignKey("ColorCollection", on_delete=models.SET_NULL, null=True, blank=True)
    available_finishes = models.ManyToManyField("Finish", blank=True, related_name="colors")
    recommended_surfaces = models.ManyToManyField("Surface", blank=True, related_name="colors")
    recommended_rooms = models.ManyToManyField("RoomType", blank=True, related_name="colors")
    inspiration_images = models.ManyToManyField("ColorImage", blank=True, related_name="colors")

    coverage_per_liter = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    drying_time_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    voc_level = models.CharField(max_length=50, blank=True, null=True)

    main_image = models.ImageField(upload_to="colors/swatches/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colors"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        # Automatically generate slug if not set
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.code}")
            slug = base_slug
            # Ensure uniqueness
            counter = 1
            while Color.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug[:150]  # truncate safely
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("color_detail", args=[self.slug])


class SavedColor(models.Model):
    """
    Stores colors that users have saved (favorites/bookmarks).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_colors"
    )
    color = models.ForeignKey(
        Color, on_delete=models.CASCADE, related_name="saved_by_users"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "color")
        ordering = ["-saved_at"]
        verbose_name = "Saved Color"
        verbose_name_plural = "Saved Colors"

    def __str__(self):
        return f"{self.user} saved {self.color.name}"
