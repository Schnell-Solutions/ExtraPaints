import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models.base import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from ideas.models import SavedIdea
from core.services.rate_limit import rate_limit

from .forms import (
    AccountDeletionRequestForm,
    OTPCodeForm,
    PasswordChangeCompleteForm,
    PasswordChangeStartForm,
    PasswordResetCompleteForm,
    PasswordResetRequestForm,
    ResendEmailForm,
    UserLoginForm,
    UserRegisterForm,
    UserUpdateForm,
)
from .models import AccountDeletionRequest, AuthOTP
from .services.account_deletion import submit_account_deletion_request, user_has_pending_deletion
from .services.auth_email import send_auth_otp_email
from .services.otp import create_otp, otp_ttl_seconds, verify_otp

logger = logging.getLogger(__name__)
User = get_user_model()

SESSION_VERIFY_USER = 'auth_verify_user_id'
SESSION_RESET_USER = 'auth_reset_user_id'
SESSION_RESET_VERIFIED = 'auth_reset_verified'
SESSION_CHANGE_OTP_SENT = 'auth_change_otp_sent'


def _ttl_minutes():
    return max(1, otp_ttl_seconds() // 60)


def _user_display_name(user):
    return user.full_name or user.username


def _send_user_otp(user, purpose, purpose_label):
    code = create_otp(user, purpose)
    return send_auth_otp_email(
        to_email=user.email,
        user_name=_user_display_name(user),
        purpose_label=purpose_label,
        otp_code=code,
        ttl_minutes=_ttl_minutes(),
    )


def _lookup_user_by_identifier(identifier):
    login = (identifier or '').strip()
    if not login:
        return None
    if '@' in login:
        return User.objects.filter(email__iexact=login).first()
    return User.objects.filter(username__iexact=login).first()


# -------------------------------
# EMAIL VERIFICATION (OTP)
# -------------------------------


def _issue_email_verification_otp(request, user):
    sent = _send_user_otp(user, AuthOTP.Purpose.EMAIL_VERIFY, 'email verification')
    request.session[SESSION_VERIFY_USER] = user.pk
    return sent


@rate_limit('auth_resend', limit=5, period=600)
def resend_verification(request):
    if request.method == 'POST':
        form = ResendEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email__iexact=email)
                if not user.is_email_verified:
                    _issue_email_verification_otp(request, user)
            except User.DoesNotExist:
                pass
            except Exception:
                logger.exception('Resend verification OTP error')

        messages.success(
            request,
            'If an account exists for that email, we sent a new verification code.',
        )
        return redirect('verify_email_otp')

    return render(request, 'accounts/resend_verification.html', {'form': ResendEmailForm()})


def verification_pending(request):
    return render(request, 'accounts/verification_pending.html')


@rate_limit('auth_verify_otp', limit=10, period=600)
def verify_email_otp(request):
    user = None
    user_id = request.session.get(SESSION_VERIFY_USER)
    if user_id:
        user = User.objects.filter(pk=user_id).first()

    if request.method == 'POST':
        form = OTPCodeForm(request.POST)
        if not user:
            messages.error(request, 'Your verification session expired. Please register or resend a code.')
            return redirect('resend_verification')

        if user.is_email_verified:
            request.session.pop(SESSION_VERIFY_USER, None)
            messages.info(request, 'Your email is already verified. You can sign in.')
            return redirect('login')

        if form.is_valid():
            ok, err = verify_otp(user, AuthOTP.Purpose.EMAIL_VERIFY, form.cleaned_data['code'])
            if ok:
                user.is_email_verified = True
                user.is_active = True
                user.save(update_fields=['is_email_verified', 'is_active'])
                request.session.pop(SESSION_VERIFY_USER, None)
                messages.success(request, 'Email verified successfully. You can now sign in.')
                return redirect('login')
            form.add_error('code', err)
    else:
        form = OTPCodeForm()

    masked_email = ''
    if user and user.email:
        local, _, domain = user.email.partition('@')
        if len(local) > 2:
            masked_email = f'{local[:2]}***@{domain}'
        else:
            masked_email = f'***@{domain}'

    return render(request, 'accounts/verify_email_otp.html', {
        'form': form,
        'masked_email': masked_email,
        'has_session': bool(user),
    })


def verify_email(request, token):
    """Legacy link verification — redirect users to OTP flow."""
    messages.info(
        request,
        'We now verify accounts with a one-time code. Enter the code from your email below.',
    )
    return redirect('verify_email_otp')


# -------------------------------
# AUTHENTICATION
# -------------------------------


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                _issue_email_verification_otp(request, user)
            except Exception:
                logger.exception('Registration verification OTP error')

            return redirect('verification_pending')
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@rate_limit('auth_login', limit=15, period=900)
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_email_verified:
                messages.error(
                    request,
                    'Please verify your email before signing in. Enter the code we sent you.',
                )
                request.session[SESSION_VERIFY_USER] = user.pk
                return redirect('verify_email_otp')
            login(request, user)
            return redirect('home')

        identifier = request.POST.get('username', '')
        user = _lookup_user_by_identifier(identifier)
        if user and user.check_password(request.POST.get('password', '')):
            if not user.is_email_verified or not user.is_active:
                messages.error(
                    request,
                    'Please verify your email before signing in. Enter the code we sent you.',
                )
                request.session[SESSION_VERIFY_USER] = user.pk
                return redirect('verify_email_otp')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# -------------------------------
# PROFILE & ACCOUNT MANAGEMENT
# -------------------------------


@login_required
def profile_view(request):
    saved_ideas = SavedIdea.objects.filter(user=request.user).select_related('idea')
    pending_deletion = user_has_pending_deletion(request.user)
    can_request_deletion = (
        not pending_deletion
        and not request.user.is_staff
        and not request.user.is_superuser
    )
    return render(request, 'accounts/profile.html', {
        'saved_ideas': saved_ideas,
        'pending_deletion': pending_deletion,
        'can_request_deletion': can_request_deletion,
    })


@login_required
def update_profile_view(request):
    if request.method == 'GET':
        form = UserUpdateForm(instance=request.user)
        html = render_to_string('accounts/partials/_form_base.html', {'form': form}, request=request)
        return HttpResponse(html)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Profile updated successfully!',
                'full_name': user.full_name or '',
                'email': user.email,
                'phone': user.phone or '',
            })
        html = render_to_string('accounts/partials/_form_base.html', {'form': form}, request=request)
        return JsonResponse({'status': 'error', 'html_form': html}, status=400)

    return redirect('profile')


@login_required
@rate_limit('auth_change_password', limit=8, period=600)
def change_password_view(request):
    step = 'verify' if request.session.get(SESSION_CHANGE_OTP_SENT) else 'start'

    if request.method == 'POST':
        action = request.POST.get('action', 'send_code')

        if action == 'send_code':
            form = PasswordChangeStartForm(request.user, request.POST)
            if form.is_valid():
                try:
                    _send_user_otp(
                        request.user,
                        AuthOTP.Purpose.PASSWORD_CHANGE,
                        'password change',
                    )
                    request.session[SESSION_CHANGE_OTP_SENT] = True
                    messages.success(
                        request,
                        f'We sent a verification code to {request.user.email}.',
                    )
                    return redirect('change_password')
                except Exception:
                    logger.exception('Password change OTP send error')
                    messages.error(request, 'Could not send verification code. Please try again.')
            return render(request, 'accounts/change_password.html', {
                'step': 'start',
                'start_form': form,
            })

        form = PasswordChangeCompleteForm(request.user, request.POST)
        if form.is_valid():
            ok, err = verify_otp(
                request.user,
                AuthOTP.Purpose.PASSWORD_CHANGE,
                form.cleaned_data['code'],
            )
            if not ok:
                form.add_error('code', err)
            else:
                form.save()
                update_session_auth_hash(request, request.user)
                request.session.pop(SESSION_CHANGE_OTP_SENT, None)
                messages.success(request, 'Your password has been updated.')
                return redirect('profile')

        return render(request, 'accounts/change_password.html', {
            'step': 'complete',
            'complete_form': form,
        })

    if step == 'complete':
        return render(request, 'accounts/change_password.html', {
            'step': 'complete',
            'complete_form': PasswordChangeCompleteForm(request.user),
        })

    return render(request, 'accounts/change_password.html', {
        'step': 'start',
        'start_form': PasswordChangeStartForm(request.user),
    })


@login_required
@rate_limit('account_deletion', limit=3, period=3600)
def request_account_deletion(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.error(
            request,
            'Staff accounts cannot be deleted through this form. Contact your administrator.',
        )
        return redirect('profile')

    if user_has_pending_deletion(request.user):
        messages.info(
            request,
            'You already have a pending deletion request. Contact us if you need help.',
        )
        return redirect('profile')

    if request.method == 'POST':
        form = AccountDeletionRequestForm(request.user, request.POST)
        if form.is_valid():
            submit_account_deletion_request(
                user=request.user,
                reason=form.cleaned_data.get('reason', ''),
                request=request,
            )
            logout(request)
            messages.success(
                request,
                'Your account deletion request was received. You have been signed out.',
            )
            return redirect('account_deletion_submitted')
    else:
        form = AccountDeletionRequestForm(request.user)

    return render(request, 'accounts/request_account_deletion.html', {'form': form})


def account_deletion_submitted(request):
    return render(request, 'accounts/account_deletion_submitted.html')


# -------------------------------
# PASSWORD RESET (OTP)
# -------------------------------


@rate_limit('auth_password_reset', limit=5, period=600)
def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email__iexact=email)
                _send_user_otp(user, AuthOTP.Purpose.PASSWORD_RESET, 'password reset')
                request.session[SESSION_RESET_USER] = user.pk
                request.session.pop(SESSION_RESET_VERIFIED, None)
            except ObjectDoesNotExist:
                pass
            except Exception:
                logger.exception('Password reset OTP error')

            messages.success(
                request,
                'If an account exists for that email, we sent a password reset code.',
            )
            return redirect('password_reset_done')

    return render(request, 'accounts/password_reset_request.html', {
        'form': PasswordResetRequestForm(),
    })


@rate_limit('auth_password_reset_verify', limit=10, period=600)
def password_reset_verify(request):
    user_id = request.session.get(SESSION_RESET_USER)
    user = User.objects.filter(pk=user_id).first() if user_id else None

    if not user:
        messages.error(request, 'Start by entering your email to receive a reset code.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = OTPCodeForm(request.POST)
        if form.is_valid():
            ok, err = verify_otp(user, AuthOTP.Purpose.PASSWORD_RESET, form.cleaned_data['code'])
            if ok:
                request.session[SESSION_RESET_VERIFIED] = True
                return redirect('password_reset_set')
            form.add_error('code', err)
    else:
        form = OTPCodeForm()

    return render(request, 'accounts/password_reset_verify.html', {'form': form})


def password_reset_set(request):
    if not request.session.get(SESSION_RESET_VERIFIED):
        messages.error(request, 'Please verify your reset code first.')
        return redirect('password_reset_verify')

    user_id = request.session.get(SESSION_RESET_USER)
    user = User.objects.filter(pk=user_id).first()
    if not user:
        messages.error(request, 'Your reset session expired. Please start again.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = PasswordResetCompleteForm(user, request.POST)
        if form.is_valid():
            form.save()
            request.session.pop(SESSION_RESET_USER, None)
            request.session.pop(SESSION_RESET_VERIFIED, None)
            messages.success(request, 'Your password has been updated. You can sign in now.')
            return redirect('login')
    else:
        form = PasswordResetCompleteForm(user)

    return render(request, 'accounts/password_reset_set.html', {'form': form})


def password_reset_done(request):
    return redirect('password_reset_verify')


def password_reset_confirm(request, uidb64, token):
    messages.info(
        request,
        'Password reset now uses a one-time code. Enter the code we emailed you.',
    )
    return redirect('password_reset_verify')
