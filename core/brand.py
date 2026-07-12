"""Single source of truth for customer-facing brand naming."""

from datetime import date

BRAND_NAME = 'ExtraPaints'
BRAND_TAGLINE = 'Professional paint supply & tailored quotations'
PAGE_TITLE_SUFFIX = f'| {BRAND_NAME}'

COMPANY_FOUNDED_YEAR = 2015


def company_years_experience(as_of=None):
    """Years in business from founding year; updates automatically each calendar year."""
    year = (as_of or date.today()).year
    return max(0, year - COMPANY_FOUNDED_YEAR)


def format_kenya_phone_local(value):
    """Display Kenyan mobile as 0725 752 908 from +254… or 254… digits."""
    digits = ''.join(c for c in str(value) if c.isdigit())
    if digits.startswith('254'):
        digits = f'0{digits[3:]}'
    if len(digits) >= 10 and digits.startswith('0'):
        return f'{digits[:4]} {digits[4:7]} {digits[7:10]}'
    return str(value).strip() if value else ''


def format_whatsapp_display(digits):
    """Format wa.me digits for display (local Kenyan format)."""
    return format_kenya_phone_local(digits) or ''
