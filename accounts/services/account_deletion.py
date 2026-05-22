"""Account deletion request handling — deactivate, log, notify."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from accounts.models import AccountDeletionRequest

logger = logging.getLogger(__name__)


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()[:45]
    return (request.META.get('REMOTE_ADDR') or '')[:45]


def user_has_pending_deletion(user) -> bool:
    return AccountDeletionRequest.objects.filter(
        user=user,
        status=AccountDeletionRequest.Status.PENDING,
    ).exists()


def submit_account_deletion_request(*, user, reason: str, request) -> AccountDeletionRequest:
    """
    Record deletion request, deactivate account, notify admin and user.
    Caller must log the user out after this returns.
    """
    deletion = AccountDeletionRequest.objects.create(
        user=user,
        email_snapshot=user.email,
        username_snapshot=user.username,
        full_name_snapshot=user.full_name or '',
        reason=(reason or '')[:500],
        status=AccountDeletionRequest.Status.PENDING,
        ip_address=_client_ip(request) or None,
    )

    user.is_active = False
    user.save(update_fields=['is_active'])

    _send_deletion_emails(deletion, request)
    return deletion


def _send_deletion_emails(deletion: AccountDeletionRequest, request):
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    from_email = settings.DEFAULT_FROM_EMAIL
    site_name = 'ExtraPaints'
    user_name = deletion.full_name_snapshot or deletion.username_snapshot

    user_subject = f'Account deletion request received — {site_name}'
    user_body = (
        f'Hi {user_name},\n\n'
        'We received your request to delete your ExtraPaints account. '
        'Your account has been deactivated and you have been signed out.\n\n'
        'Our team will complete data removal according to our privacy policy. '
        'If you did not request this, contact us immediately at '
        f'{getattr(settings, "BUSINESS_EMAIL", admin_email or from_email)}.\n\n'
        f'Reference: request #{deletion.pk} on {deletion.requested_at:%Y-%m-%d %H:%M UTC}.\n'
    )

    try:
        EmailMultiAlternatives(
            user_subject,
            user_body,
            from_email,
            [deletion.email_snapshot],
        ).send(fail_silently=False)
    except Exception:
        logger.exception('Failed to send account deletion confirmation to user')

    if not admin_email:
        return

    admin_subject = f'[Action required] Account deletion request — {deletion.email_snapshot}'
    admin_body = (
        f'A user requested account deletion.\n\n'
        f'Name: {deletion.full_name_snapshot or "—"}\n'
        f'Username: {deletion.username_snapshot}\n'
        f'Email: {deletion.email_snapshot}\n'
        f'Request ID: {deletion.pk}\n'
        f'IP: {deletion.ip_address or "—"}\n'
        f'Reason: {deletion.reason or "(none)"}\n\n'
        f'Review in Django admin → Account deletion requests.\n'
        f'User ID: {deletion.user_id or "detached"}\n'
    )
    try:
        EmailMultiAlternatives(
            admin_subject,
            admin_body,
            from_email,
            [admin_email],
        ).send(fail_silently=False)
    except Exception:
        logger.exception('Failed to send account deletion notice to admin')
