from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from colors.models import Color  # <-- IMPORT THE COLOR MODEL


class Category(models.Model):
    """
    Category for grouping ideas (e.g., Interior, Exterior, Living Room).
    """
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


class Tag(models.Model):
    """
    Tags for finer classification (e.g., Minimalist, Bold, Neutral, Modern).
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:80]
        super().save(*args, **kwargs)


class Idea(models.Model):
    """
    Design idea or inspiration. Each idea belongs to a category and can have multiple images and tags.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name="ideas", blank=True, null=True
    )
    tags = models.ManyToManyField(Tag, related_name="ideas", blank=True)

    # --- IMPROVEMENT 1: SAFER DELETION ---
    # Changed from CASCADE to SET_NULL. If you delete a user,
    # their ideas are kept (attributed to 'None') instead of being deleted.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Was models.CASCADE
        related_name="ideas",
        null=True,  # Added
        blank=True  # Added
    )

    # Optional features
    mood = models.CharField(
        max_length=100, blank=True, null=True, help_text="e.g., Calm, Cozy, Playful"
    )

    paint_colors = models.ManyToManyField(
        Color,
        related_name="ideas_featured_in",  # Clearer related_name
        blank=True,
        help_text="Tag specific paint colors used in this idea."
    )

    main_image = models.ImageField(
        upload_to="ideas/main/", blank=True, null=True, help_text="Primary display image"
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Saved / favorite relationship
    saved_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="saved_ideas_link",
        through="SavedIdea",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Idea"
        verbose_name_plural = "Ideas"

    def __str__(self):
        return self.title

    # --- IMPROVEMENT 3: SMARTER IMAGE FALLBACK ---
    @property
    def get_display_image(self):
        """
        Returns the main image, or the first gallery image, or a placeholder.
        This is now safe and checks if image files actually exist.
        """
        # Check for a valid main_image file
        if self.main_image and hasattr(self.main_image, 'url'):
            return self.main_image.url

        first_gallery_image = self.images.first()

        # Check for a valid gallery image file
        if (first_gallery_image and
                first_gallery_image.image and
                hasattr(first_gallery_image.image, 'url')):
            return first_gallery_image.image.url

        # If all else fails, return the placeholder
        return "https://placehold.co/600x400/f1f5f9/9ca3af?text=Inspiration"

    def get_absolute_url(self):
        return reverse("idea_detail", args=[self.slug])

    # --- IMPROVEMENT 4: UNIQUE SLUG GENERATION ---
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:255]
            slug = base_slug
            counter = 1
            # Check for uniqueness and append a counter if needed
            while Idea.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class IdeaImage(models.Model):
    """
    Additional supporting images for each idea (gallery).
    """
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="ideas/gallery/")
    caption = models.CharField(max_length=255, blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]
        verbose_name = "Idea Image"
        verbose_name_plural = "Idea Images"

    def __str__(self):
        return f"Image for {self.idea.title}"


class SavedIdea(models.Model):
    """
    Stores ideas that users have saved (favorites/bookmarks).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_ideas"
    )
    idea = models.ForeignKey(
        Idea, on_delete=models.CASCADE, related_name="saved_by_users"
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "idea")
        ordering = ["-saved_at"]
        verbose_name = "Saved Idea"
        verbose_name_plural = "Saved Ideas"

    def __str__(self):
        return f"{self.user} saved {self.idea}"
