from django.db import models

class NewsletterSubscriber(models.Model):
    """Stores email addresses of newsletter subscribers."""
    email = models.EmailField(unique=True, max_length=150)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"


class Newsletter(models.Model):
    """Represents a specific newsletter edition to be sent."""
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="The main content of the newsletter. Use HTML if needed.")
    created_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ['-created_at']