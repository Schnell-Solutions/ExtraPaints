import re
import secrets

from django.db import transaction


_CODE_PATTERN = re.compile(r'^[A-Z0-9]{2,12}-[A-Z0-9]{4}$')
# Unambiguous chars (no 0/O, 1/I/L) for readable partner codes
_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def normalize_referral_code(raw: str) -> str:
    return (raw or '').strip().upper().replace(' ', '')


def is_valid_code_format(code: str) -> bool:
    return bool(code and _CODE_PATTERN.match(code))


def _name_token(name: str) -> str:
    """First word of partner name, letters only (e.g. Sarah Okello → SARAH)."""
    parts = re.findall(r'[A-Za-z]+', name or '')
    token = parts[0] if parts else 'PARTNER'
    return token[:12].upper()


def _random_suffix(length: int = 4) -> str:
    return ''.join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def generate_referral_code(name: str, *, max_attempts: int = 30) -> str:
    """
    Professional partner code: PREFIX-XXXX
    PREFIX from partner name; XXXX = 4 unambiguous uppercase alphanumeric chars.
    Example: Sarah Okello → SARAH-K7M2
    """
    from .models import Affiliate

    prefix = _name_token(name)
    for _ in range(max_attempts):
        code = f'{prefix}-{_random_suffix()}'
        if is_valid_code_format(code) and not Affiliate.objects.filter(code=code).exists():
            return code
    fallback = f'{prefix}-{_random_suffix(6)}'[: len(prefix) + 1 + 4]
    return fallback


def regenerate_code_for_affiliate(affiliate) -> str:
    from .models import Affiliate

    with transaction.atomic():
        for _ in range(30):
            code = generate_referral_code(affiliate.name)
            if not Affiliate.objects.filter(code=code).exclude(pk=affiliate.pk).exists():
                affiliate.code = code
                affiliate.save(update_fields=['code', 'updated_at'])
                return code
    raise ValueError('Could not generate a unique referral code.')
