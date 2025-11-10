from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.db.models.base import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponse

from ideas.models import SavedIdea
from .forms import UserRegisterForm, UserLoginForm, UserUpdateForm

User = get_user_model()
signer = TimestampSigner()


# -------------------------------
# EMAIL VERIFICATION
# -------------------------------

def resend_verification(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                return redirect('login')

            token = signer.sign(user.pk)
            verify_url = request.build_absolute_uri(f"/accounts/verify/{token}/")

            subject = "Resend: Verify your email - ExtraPaints"
            context = {
                'user_name': user.full_name or user.username,
                'verify_url': verify_url,
                'site_name': 'ExtraPaints',
            }

            html_content = render_to_string('accounts/verification_email_html.html', context)
            plain_message = f"Click the link to verify your email:\n{verify_url}"

            msg = EmailMultiAlternatives(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, "Verification email resent successfully.")
        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")
        except Exception as e:
            print(f"Resend email error: {e}")
            messages.error(request, "Unable to send verification email. Try again later.")

        return redirect('login')

    return render(request, 'accounts/resend_verification.html')


def verify_email(request, token):
    try:
        user_id = signer.unsign(token, max_age=60 * 60 * 24)
        user = User.objects.get(pk=user_id)

        if not user.is_email_verified:
            user.is_email_verified = True
            user.is_active = True
            user.save()
            messages.success(request, "Your email has been verified! You can now log in.")
        else:
            messages.info(request, "Your email was already verified.")
    except SignatureExpired:
        messages.error(request, "The verification link has expired.")
        return redirect('resend_verification')
    except (BadSignature, User.DoesNotExist):
        messages.error(request, "Invalid verification link.")

    return redirect('login')


# -------------------------------
# AUTHENTICATION
# -------------------------------

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            token = signer.sign(user.pk)
            verify_url = request.build_absolute_uri(f"/accounts/verify/{token}/")

            subject = "Verify your email - ExtraPaints"
            context = {
                'user_name': user.full_name or user.username,
                'verify_url': verify_url,
                'site_name': 'ExtraPaints',
            }

            html_content = render_to_string('accounts/verification_email_html.html', context)
            plain_message = f"Hi {context['user_name']},\nPlease verify your email:\n{verify_url}"

            try:
                msg = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            except Exception as e:
                print(f"Email send error: {e}")

            return redirect('verification_pending')
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_email_verified:
                messages.error(request, "Please verify your email before logging in.")
                return redirect('login')
            login(request, user)
            return redirect('home')
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
    return render(request, 'accounts/profile.html', {'saved_ideas': saved_ideas})


def verification_pending(request):
    return render(request, 'accounts/verification_pending.html')


@login_required
def update_profile_view(request):
    """Handles AJAX GET and POST for profile update."""
    if request.method == "GET":
        form = UserUpdateForm(instance=request.user)
        html = render_to_string("accounts/partials/_form_base.html", {"form": form}, request=request)
        return HttpResponse(html)

    elif request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            return JsonResponse({
                "status": "success",
                "message": "Profile updated successfully!",
                "full_name": user.full_name or "",
                "email": user.email,
                "phone": user.phone or ""
            })
        else:
            html = render_to_string("accounts/partials/_form_base.html", {"form": form}, request=request)
            return JsonResponse({"status": "error", "html_form": html}, status=400)

    return redirect("profile")


@login_required
def change_password_view(request):
    """Handles AJAX GET and POST for password change."""
    if request.method == "GET":
        form = PasswordChangeForm(request.user)
        html = render_to_string("accounts/partials/_form_base.html", {"form": form}, request=request)
        return HttpResponse(html)

    elif request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            return JsonResponse({"status": "success", "message": "Password changed successfully!"})
        else:
            html = render_to_string("accounts/partials/_form_base.html", {"form": form}, request=request)
            return JsonResponse({"status": "error", "html_form": html}, status=400)

    return redirect("profile")

# -------------------------------
# PASSWORD RESET
# -------------------------------

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['email']
            try:
                user = User.objects.get(email=data)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(f"/accounts/password_reset_confirm/{uid}/{token}/")

                subject = "Password Reset Requested - ExtraPaints"
                context = {
                    'user_name': user.full_name or user.username,
                    'reset_url': reset_url,
                    'site_name': 'ExtraPaints',
                }

                html_content = render_to_string('accounts/password_reset_email_html.html', context)
                plain_message = f"Click the link to reset your password:\n{reset_url}"

                msg = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()

            except ObjectDoesNotExist:
                pass
            except Exception as e:
                print(f"Password reset email error: {e}")

            # Redirect immediately, no extra message — next page explains it
            return redirect("password_reset_done")

    else:
        form = PasswordResetForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form, 'title': 'Request Password Reset'})


def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html', {'title': 'Password Reset Email Sent'})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been set. You may now log in.')
                return redirect('login')
        else:
            form = SetPasswordForm(user)
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('password_reset_request')

    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'title': 'Set New Password'})
