from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from products.models import Product
from colors.models import Color


class PortfolioProject(models.Model):
    """Represents a completed project showcasing company paints in real-world use."""

    PROJECT_TYPES = [
        ("residential", "Residential"),
        ("commercial", "Commercial"),
        ("industrial", "Industrial"),
        ("institutional", "Institutional"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    project_type = models.CharField(max_length=50, choices=PROJECT_TYPES, default="residential")
    location = models.CharField(max_length=255, blank=True, null=True)
    client_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    products_used = models.ManyToManyField(Product, blank=True, related_name="portfolio_projects")
    colors_used = models.ManyToManyField(Color, blank=True, related_name="portfolio_projects")

    completion_date = models.DateField(blank=True, null=True)
    featured_image = models.ImageField(upload_to="portfolio/featured/", blank=True, null=True)

    # --- IMPROVEMENT 1: REMOVED M2M ---
    # gallery_images = models.ManyToManyField("PortfolioImage", blank=True, related_name="projects")
    # This is now handled by the ForeignKey in PortfolioImage, just like in your Idea model.

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Portfolio Project"
        verbose_name_plural = "Portfolio Projects"
        ordering = ["-created_at"]

    # --- IMPROVEMENT 2: ADDED SAFE IMAGE FALLBACK ---
    @property
    def get_display_image(self):
        """
        Returns the featured image, or the first gallery image, or a placeholder.
        Safely checks if image files actually exist.
        """
        # Check for a valid featured_image file
        if self.featured_image and hasattr(self.featured_image, 'url'):
            return self.featured_image.url

        # Use the new related_name 'gallery_images' from the PortfolioImage model
        first_gallery_image = self.gallery_images.first()

        # Check for a valid gallery image file
        if (first_gallery_image and
                first_gallery_image.image and
                hasattr(first_gallery_image.image, 'url')):
            return first_gallery_image.image.url

        # If all else fails, return the placeholder
        return "https://placehold.co/600x400/f1f5f9/9ca3af?text=Project"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # This unique slug logic is correct
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while PortfolioProject.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # Make sure you have a 'portfolio_detail' URL name in your urls.py
        return reverse("portfolio_detail", args=[self.slug])


class PortfolioImage(models.Model):
    """
    Extra images for portfolio projects.
    This now links directly *to* a PortfolioProject.
    """

    # --- IMPROVEMENT 1: GALLERY STRUCTURE (matches IdeaImage) ---
    project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="gallery_images"  # This is used by get_display_image
    )

    image = models.ImageField(upload_to="portfolio/gallery/")
    caption = models.CharField(max_length=255, blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Portfolio Image"
        verbose_name_plural = "Portfolio Images"
        ordering = ["display_order"]  # Now correctly ordered

    def __str__(self):
        return self.caption or f"Image for {self.project.title}"
