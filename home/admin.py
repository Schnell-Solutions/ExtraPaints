from django.contrib import admin, messages
from django.utils import timezone
from .models import Newsletter, NewsletterSubscriber
# You'll create this function in views.py
from .views import send_newsletter_email


# --- Admin Action for Sending Newsletters ---

@admin.action(description='Send selected Newsletter to all subscribers')
def send_newsletter(modeladmin, request, queryset):
    """
    Triggers the sending of the selected newsletters to all active subscribers.
    """
    if queryset.filter(is_sent=True).exists():
        messages.error(request, "Cannot send newsletters that have already been marked as sent.")
        return

    # Assuming we only process the first selected item to avoid mail bomb chaos
    newsletter = queryset.first()

    # This is where the heavy lifting happens, calling the function from views.py
    success_count, error_count = send_newsletter_email(newsletter)

    if success_count > 0:
        # Update the newsletter object status
        newsletter.is_sent = True
        newsletter.sent_at = timezone.now()
        newsletter.save()

    messages.success(request,
                     f"Newsletter '{newsletter.subject}' sent! {success_count} emails successfully delivered. ({error_count} errors)."
                     )

    # Return 0 to prevent Django from showing "Successfully sent..." message
    return 0


send_newsletter.short_description = "Send selected Newsletter"


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'is_sent', 'sent_at')
    actions = [send_newsletter]
    readonly_fields = ('is_sent', 'sent_at')


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_subscribed')
    search_fields = ('email',)