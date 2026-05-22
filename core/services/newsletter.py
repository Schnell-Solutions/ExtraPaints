"""Batched newsletter delivery to avoid oversized BCC headers."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def send_newsletter_batched(newsletter, *, batch_size=BATCH_SIZE):
    """
    Send newsletter HTML to subscribers in BCC batches.
    Returns (sent_count, failed_count).
    """
    from home.models import NewsletterSubscriber

    recipient_list = list(
        NewsletterSubscriber.objects.exclude(email='').values_list('email', flat=True)
    )
    if not recipient_list:
        return 0, 0

    html_content = render_to_string('home/newsletter_email.html', {
        'subject': newsletter.subject,
        'body': newsletter.body,
        'site_name': 'ExtraPaints',
    })
    text_content = f'{newsletter.subject}\n\n{newsletter.body}'
    visible_to = settings.SALES_TEAM_EMAIL or settings.DEFAULT_FROM_EMAIL or recipient_list[0]

    sent = 0
    failed = 0

    for i in range(0, len(recipient_list), batch_size):
        batch = recipient_list[i:i + batch_size]
        try:
            msg = EmailMultiAlternatives(
                newsletter.subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [visible_to],
                bcc=batch,
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=False)
            sent += len(batch)
        except Exception:
            logger.exception('Newsletter batch failed (%s-%s)', i, i + len(batch))
            failed += len(batch)

    return sent, failed
