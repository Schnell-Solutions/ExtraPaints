import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class InquiryEmailService:
    """Send branded inquiry emails (contact, quote, etc.) with consistent error logging."""

    @staticmethod
    def send(
        *,
        subject: str,
        text_body: str,
        html_template: str,
        html_context: dict | None = None,
        recipient: str | None = None,
    ) -> bool:
        recipient = recipient or settings.SALES_TEAM_EMAIL
        context = {
            'subject': subject,
            'content': text_body,
            'site_name': 'ExtraPaints',
            **(html_context or {}),
        }
        try:
            html_content = render_to_string(html_template, context)
            msg = EmailMultiAlternatives(
                subject,
                text_body,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=False)
            return True
        except Exception:
            logger.exception('Failed to send inquiry email: %s', subject)
            return False

    @staticmethod
    def send_customer_confirmation(
        *,
        to_email: str,
        subject: str,
        html_template: str,
        html_context: dict | None = None,
    ) -> bool:
        context = {
            'site_name': 'ExtraPaints',
            **(html_context or {}),
        }
        try:
            html_content = render_to_string(html_template, context)
            text_body = context.get('plain_text', subject)
            msg = EmailMultiAlternatives(
                subject,
                text_body,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send(fail_silently=False)
            return True
        except Exception:
            logger.exception('Failed to send customer confirmation to %s', to_email)
            return False
