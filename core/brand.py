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


def format_whatsapp_display(digits):
    """Format wa.me digits (e.g. 254750422863) for display."""
    digits = ''.join(c for c in str(digits) if c.isdigit())
    if digits.startswith('254') and len(digits) >= 12:
        return f'+{digits[:3]} {digits[3:6]} {digits[6:9]} {digits[9:]}'
    return f'+{digits}' if digits else ''
