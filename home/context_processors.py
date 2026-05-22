import os

from django.conf import settings

from datetime import date

from core.brand import (
    BRAND_NAME,
    PAGE_TITLE_SUFFIX,
    company_years_experience,
    format_whatsapp_display,
)
from core.seo.constants import (
    DEFAULT_META_DESCRIPTION,
    DEFAULT_OG_DESCRIPTION,
    DEFAULT_SITE_TITLE,
    NOINDEX_URL_NAMES,
)
from core.seo.schema import local_business_json, organization_json, website_search_json


def media_url(request):
    return {
        'MEDIA_URL': settings.MEDIA_URL,
    }


def canonical_url(request):
    """Path-only canonical URL (no query string) to reduce duplicate URL signals."""
    public = getattr(settings, 'PUBLIC_SITE_URL', '').rstrip('/')
    if public:
        site_root = public
        canonical = f'{public}{request.path}'
    else:
        site_root = request.build_absolute_uri('/').rstrip('/')
        canonical = request.build_absolute_uri(request.path)
    return {
        'canonical_url': canonical,
        'site_root_url': site_root,
    }


def site_settings(request):
    return {
        'use_tailwind_cdn': getattr(settings, 'USE_TAILWIND_CDN', False),
        'brand_name': BRAND_NAME,
        'page_title_suffix': PAGE_TITLE_SUFFIX,
        'static_version': getattr(settings, 'STATIC_VERSION', '1'),
    }


def conversion_context(request):
    """Business contact details and B2B conversion copy used sitewide."""
    cfg = getattr(settings, 'SEO_LOCAL_BUSINESS', {})
    primary_phone = cfg.get('telephone', [getattr(settings, 'BUSINESS_PHONE_PRIMARY', '+254729086036')])
    if isinstance(primary_phone, list):
        primary_phone = primary_phone[0] if primary_phone else '+254729086036'
    secondary = getattr(settings, 'BUSINESS_PHONE_SECONDARY', '+254725752908')
    whatsapp_number = getattr(settings, 'BUSINESS_WHATSAPP', '254750422863')
    founded_year = getattr(settings, 'COMPANY_FOUNDED_YEAR', 2015)
    return {
        'business_phone_primary': primary_phone,
        'business_phone_secondary': secondary,
        'business_email': cfg.get('email', getattr(settings, 'BUSINESS_EMAIL', 'info@extrapaints.co.ke')),
        'business_whatsapp_url': f'https://wa.me/{whatsapp_number}',
        'business_whatsapp_display': format_whatsapp_display(whatsapp_number),
        'company_founded_year': founded_year,
        'company_years_experience': company_years_experience(date.today()),
        'company_projects_count': '3,000+',
        'response_time_label': getattr(settings, 'QUOTE_RESPONSE_SLA', 'Response within 24 hours'),
        'showroom_nairobi': getattr(settings, 'SHOWROOM_NAIROBI', f"{cfg.get('city', 'Nairobi')}, Kenya"),
        'showroom_eldoret': getattr(settings, 'SHOWROOM_ELDORET', 'Eldoret, Kenya'),
        'site_tagline_b2b': (
            'Professional paint supply & tailored quotations for contractors and distributors.'
        ),
        'google_maps_url': cfg.get('google_maps_url', ''),
        'local_address_line': _format_address(cfg),
        'social_facebook': os.getenv(
            'SOCIAL_FACEBOOK',
            'https://web.facebook.com/extrapaints.ke',
        ),
        'social_linkedin': os.getenv(
            'SOCIAL_LINKEDIN',
            'https://www.linkedin.com/in/extrapaints-ltd-b5a2283a3',
        ),
        'social_instagram': os.getenv(
            'SOCIAL_INSTAGRAM',
            'https://www.instagram.com/extrapaints400/',
        ),
    }


def _format_address(cfg):
    parts = [
        cfg.get('street_address'),
        cfg.get('city', 'Nairobi'),
        cfg.get('region'),
        cfg.get('country_name', 'Kenya'),
    ]
    return ', '.join(p for p in parts if p)


def csp_nonce(request):
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}


def referral_context(request):
    from affiliates.services import referral_context_for_request

    return referral_context_for_request(request)


def seo_context(request):
    """Global SEO: defaults, structured data, noindex rules."""
    match = getattr(request, 'resolver_match', None)
    url_name = match.url_name if match else None
    page_noindex = url_name in NOINDEX_URL_NAMES

    return {
        'seo_default_title': DEFAULT_SITE_TITLE,
        'seo_default_description': DEFAULT_META_DESCRIPTION,
        'seo_default_og_description': DEFAULT_OG_DESCRIPTION,
        'page_noindex': page_noindex,
        'local_business_json_ld': local_business_json(request),
        'website_search_json_ld': website_search_json(request),
        'organization_json_ld': organization_json(request),
    }
