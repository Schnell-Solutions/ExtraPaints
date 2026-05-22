import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from accounts.models import AuthOTP

logger = logging.getLogger(__name__)


def otp_length():
    return int(getattr(settings, 'AUTH_OTP_LENGTH', 6))


def otp_ttl_seconds():
    return int(getattr(settings, 'AUTH_OTP_TTL_SECONDS', 900))


def otp_max_attempts():
    return int(getattr(settings, 'AUTH_OTP_MAX_ATTEMPTS', 5))


def hash_otp_code(code: str) -> str:
    normalized = ''.join(ch for ch in str(code).strip() if ch.isdigit())
    payload = f'{settings.SECRET_KEY}:{normalized}'
    return hashlib.sha256(payload.encode()).hexdigest()


def generate_otp_code() -> str:
    length = otp_length()
    return ''.join(secrets.choice('0123456789') for _ in range(length))


def invalidate_otps(user, purpose):
    AuthOTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)


def create_otp(user, purpose) -> str:
    """Create a new OTP for the user; returns the plain code (for email only)."""
    invalidate_otps(user, purpose)
    code = generate_otp_code()
    AuthOTP.objects.create(
        user=user,
        purpose=purpose,
        code_hash=hash_otp_code(code),
        expires_at=timezone.now() + timedelta(seconds=otp_ttl_seconds()),
    )
    return code


def verify_otp(user, purpose, code: str) -> tuple[bool, str]:
    """
    Verify a submitted OTP. Returns (success, error_message).
    """
    normalized = ''.join(ch for ch in str(code).strip() if ch.isdigit())
    if len(normalized) != otp_length():
        return False, f'Enter the {otp_length()}-digit code from your email.'

    otp = (
        AuthOTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
        )
        .order_by('-created_at')
        .first()
    )

    if not otp:
        return False, 'No active verification code found. Request a new code.'

    if timezone.now() > otp.expires_at:
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        return False, 'This code has expired. Request a new one.'

    if otp.attempts >= otp_max_attempts():
        otp.is_used = True
        otp.save(update_fields=['is_used'])
        return False, 'Too many incorrect attempts. Request a new code.'

    if otp.code_hash != hash_otp_code(normalized):
        otp.attempts += 1
        otp.save(update_fields=['attempts'])
        remaining = otp_max_attempts() - otp.attempts
        if remaining <= 0:
            otp.is_used = True
            otp.save(update_fields=['is_used'])
            return False, 'Too many incorrect attempts. Request a new code.'
        return False, f'Incorrect code. {remaining} attempt(s) remaining.'

    otp.is_used = True
    otp.save(update_fields=['is_used'])
    return True, ''
