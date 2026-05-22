"""Referral attribution — server-validated, optional, non-blocking."""

import logging

from django.conf import settings
from django.core import signing

from affiliates.models import Affiliate, ReferralLead, ReferralVisit
from affiliates.utils import normalize_referral_code

logger = logging.getLogger(__name__)

SESSION_AFFILIATE_ID = 'referral_affiliate_id'
SESSION_AFFILIATE_CODE = 'referral_affiliate_code'
COOKIE_NAME = 'ep_ref'
COOKIE_SALT = 'extrapaints.referral.v1'
COOKIE_MAX_AGE = getattr(settings, 'REFERRAL_COOKIE_MAX_AGE', 60 * 60 * 24 * 60)


def resolve_active_affiliate(code: str):
    normalized = normalize_referral_code(code)
    if not normalized:
        return None
    return Affiliate.objects.filter(code=normalized, is_active=True).first()


def bind_referral_to_request(request, affiliate, *, log_visit=False, landing_path=''):
    """Store validated affiliate on session + signed cookie (first-touch friendly)."""
    if not affiliate or not affiliate.is_active:
        return

    request.session[SESSION_AFFILIATE_ID] = affiliate.pk
    request.session[SESSION_AFFILIATE_CODE] = affiliate.code
    request.session.modified = True

    if log_visit:
        try:
            ReferralVisit.objects.create(
                affiliate=affiliate,
                session_key=(request.session.session_key or '')[:64],
                ip_address=_client_ip(request),
                landing_path=(landing_path or '')[:500],
            )
        except Exception:
            logger.exception('Failed to log referral visit')

    return affiliate


def capture_referral_from_query(request):
    """Process ?ref=CODE on GET — validate server-side, do not trust cookie alone."""
    raw = request.GET.get('ref', '')
    if not raw:
        return _restore_from_signed_cookie(request)

    affiliate = resolve_active_affiliate(raw)
    if not affiliate:
        return None

    bind_referral_to_request(
        request,
        affiliate,
        log_visit=True,
        landing_path=request.path,
    )
    return affiliate


def _restore_from_signed_cookie(request):
    if request.session.get(SESSION_AFFILIATE_ID):
        aff = Affiliate.objects.filter(
            pk=request.session[SESSION_AFFILIATE_ID],
            is_active=True,
        ).first()
        if aff:
            return aff
        clear_referral_session(request)

    signed = request.COOKIES.get(COOKIE_NAME)
    if not signed:
        return None
    try:
        affiliate_id = signing.loads(signed, salt=COOKIE_SALT, max_age=COOKIE_MAX_AGE)
        affiliate = Affiliate.objects.filter(pk=affiliate_id, is_active=True).first()
        if affiliate:
            bind_referral_to_request(request, affiliate)
            return affiliate
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        pass
    return None


def get_session_affiliate(request):
    aid = request.session.get(SESSION_AFFILIATE_ID)
    if not aid:
        return None
    return Affiliate.objects.filter(pk=aid, is_active=True).first()


def clear_referral_session(request):
    request.session.pop(SESSION_AFFILIATE_ID, None)
    request.session.pop(SESSION_AFFILIATE_CODE, None)
    request.session.modified = True


def set_referral_cookie(response, affiliate):
    if affiliate and affiliate.is_active:
        response.set_cookie(
            COOKIE_NAME,
            signing.dumps(affiliate.pk, salt=COOKIE_SALT),
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG,
        )
    else:
        response.delete_cookie(COOKIE_NAME)
    return response


def process_referral_on_post(request):
    """
    Resolve affiliate for a form submission.
    Returns (affiliate|None, referral_invalid: bool).
    """
    if request.POST.get('skip_referral') == '1':
        return None, False

    posted = normalize_referral_code(request.POST.get('referral_code', ''))
    if posted:
        affiliate = resolve_active_affiliate(posted)
        if affiliate:
            bind_referral_to_request(request, affiliate)
            return affiliate, False
        return None, True

    return get_session_affiliate(request), False


def posted_referral_code(request) -> str:
    return normalize_referral_code(request.POST.get('referral_code', ''))


def referral_email_line(affiliate) -> str:
    if not affiliate:
        return ''
    return (
        f'\nReferral partner: {affiliate.name} (code {affiliate.code})\n'
        f'Partner contact: {affiliate.email}'
    )


def record_referral_lead(
    *,
    affiliate,
    lead_type: str,
    customer_name: str,
    customer_email: str = '',
    customer_phone: str = '',
    message_excerpt: str = '',
    request=None,
):
    if not affiliate:
        return None
    try:
        return ReferralLead.objects.create(
            affiliate=affiliate,
            lead_type=lead_type,
            customer_name=customer_name[:200],
            customer_email=(customer_email or '')[:254],
            customer_phone=(customer_phone or '')[:30],
            message_excerpt=(message_excerpt or '')[:500],
            referral_code_used=affiliate.code,
            session_key=((request.session.session_key if request else '') or '')[:64],
        )
    except Exception:
        logger.exception('Failed to record referral lead')
        return None


def referral_context_for_request(request):
    affiliate = get_session_affiliate(request)
    if not affiliate:
        _restore_from_signed_cookie(request)
        affiliate = get_session_affiliate(request)
    return {
        'referral_partner': affiliate,
        'referral_code_prefill': request.session.get(SESSION_AFFILIATE_CODE, ''),
        'show_referral_partner_note': bool(affiliate),
    }


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()[:45]
    return (request.META.get('REMOTE_ADDR') or '')[:45]
