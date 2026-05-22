from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from colors.models import Color
from core.html_sanitize import sanitize_html
from products.models import Product


class Guide(models.Model):
    GUIDE_TYPES = [
        ('article', 'Article'),
        ('howto', 'How-To'),
        ('faq', 'FAQ'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    guide_type = models.CharField(max_length=20, choices=GUIDE_TYPES, default='article')
    excerpt = models.TextField(help_text='Short summary for listings and meta description fallback.')
    body = models.TextField()
    meta_description = models.CharField(max_length=320, blank=True)

    faq_items = models.JSONField(
        default=list,
        blank=True,
        help_text='List of {"question": "...", "answer": "..."} objects.',
    )
    howto_steps = models.JSONField(
        default=list,
        blank=True,
        help_text='List of {"name": "...", "text": "..."} for HowTo schema.',
    )
    howto_total_time = models.CharField(
        max_length=30,
        blank=True,
        default='PT1H',
        help_text='ISO 8601 duration, e.g. PT30M, PT1H',
    )

    related_products = models.ManyToManyField(Product, blank=True, related_name='guides')
    related_colors = models.ManyToManyField(Color, blank=True, related_name='guides')

    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-updated_at']
        verbose_name = 'Guide'
        verbose_name_plural = 'Guides'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.body:
            self.body = sanitize_html(self.body)
        if not self.slug:
            base = slugify(self.title)[:160]
            slug = base
            n = 1
            while Guide.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('guide_detail', args=[self.slug])

    @property
    def seo_description(self):
        return (self.meta_description or self.excerpt or '')[:320]
