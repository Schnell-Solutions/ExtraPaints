import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_auth_otp_email(*, to_email: str, user_name: str, purpose_label: str, otp_code: str, ttl_minutes: int):
    """Send a branded OTP email for verification, password reset, or password change."""
    subject_map = {
        'email verification': 'Verify your email — ExtraPaints',
        'password reset': 'Password reset code — ExtraPaints',
        'password change': 'Password change code — ExtraPaints',
    }
    subject = subject_map.get(purpose_label.lower(), 'Your verification code — ExtraPaints')

    context = {
        'user_name': user_name,
        'otp_code': otp_code,
        'purpose_label': purpose_label,
        'ttl_minutes': ttl_minutes,
        'site_name': 'ExtraPaints',
    }

    html_content = render_to_string('accounts/otp_email_html.html', context)
    plain_message = (
        f'Hello {user_name},\n\n'
        f'Your {purpose_label} code is: {otp_code}\n\n'
        f'This code expires in {ttl_minutes} minutes.\n\n'
        f'If you did not request this, you can ignore this email.\n\n'
        f'The ExtraPaints Team'
    )

    try:
        msg = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        return True
    except Exception:
        logger.exception('Auth OTP email failed for %s', to_email)
        return False
