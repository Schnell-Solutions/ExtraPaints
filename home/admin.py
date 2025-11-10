from django.contrib import admin, messages
from django.utils import timezone
from .models import Newsletter, NewsletterSubscriber
from .views import send_newsletter_email  # make sure this function exists in views.py


# --- Custom Admin Action for Sending Newsletters ---
@admin.action(description="Send selected newsletter to all subscribers")
def send_newsletter(modeladmin, request, queryset):
    """
    Sends the selected newsletter(s) to all subscribers.
    Restricts to one selection at a time to avoid confusion.
    """
    if queryset.count() > 1:
        messages.error(request, "Please select only one newsletter to send at a time.")
        return

    newsletter = queryset.first()

    if newsletter.is_sent:
        messages.warning(request, f"'{newsletter.subject}' has already been sent.")
        return

    try:
        success_count, error_count = send_newsletter_email(newsletter)

        if success_count > 0:
            newsletter.is_sent = True
            newsletter.sent_at = timezone.now()
            newsletter.save()

        messages.success(
            request,
            f"✅ Newsletter '{newsletter.subject}' sent successfully! "
            f"{success_count} delivered, {error_count} failed."
        )
    except Exception as e:
        messages.error(request, f"❌ Failed to send newsletter: {str(e)}")


# --- Newsletter Admin ---
@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("subject", "is_sent", "created_at", "sent_at")
    list_filter = ("is_sent", "created_at")
    search_fields = ("subject", "body")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "sent_at")
    actions = [send_newsletter]
    list_per_page = 25

    fieldsets = (
        ("Newsletter Content", {
            "fields": ("subject", "body"),
        }),
        ("Status & Timing", {
            "fields": ("is_sent", "sent_at", "created_at"),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Lock fields after the newsletter has been sent."""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_sent:
            readonly.extend(["subject", "body", "is_sent"])
        return readonly


# --- Newsletter Subscriber Admin ---
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "date_subscribed")
    search_fields = ("email",)
    ordering = ("-date_subscribed",)
    readonly_fields = ("date_subscribed",)
    list_per_page = 25

    fieldsets = (
        ("Subscriber Information", {
            "fields": ("email",),
        }),
        ("Subscription Details", {
            "fields": ("date_subscribed",),
        }),
    )
