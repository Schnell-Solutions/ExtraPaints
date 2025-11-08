from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from ideas.models import SavedIdea
from .forms import UserRegisterForm, UserLoginForm

User = get_user_model()

signer = TimestampSigner()


def resend_verification(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                messages.info(request, "Your email is already verified.")
                return redirect('login')

            token = signer.sign(user.pk)
            verify_url = request.build_absolute_uri(f"/accounts/verify/{token}/")

            # --- Email Styling Logic (Resend) ---
            subject = "Resend: Verify your email - ExtraPaints"
            context = {
                'user_name': user.full_name or user.username,
                'verify_url': verify_url,
                'site_name': 'ExtraPaints',
            }
            html_content = render_to_string('accounts/verification_email_html.html', context)
            plain_message = f"Click the link to verify your email:\n{verify_url}"
            # ------------------------------------

            try:
                msg = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                messages.success(request, "A new verification email has been sent.")
            except Exception as e:
                print(f"Resend email error: {e}")
                messages.error(request, "An error occurred while sending the verification email.")

        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")
        return redirect('login')

    return render(request, 'accounts/resend_verification.html')

def verify_email(request, token):
    try:
        # Validate and extract user ID
        user_id = signer.unsign(token, max_age=60 * 60 * 24)  # 24-hour expiry
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


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            token = signer.sign(user.pk)
            verify_url = request.build_absolute_uri(f"/accounts/verify/{token}/")

            # --- Email Styling Logic (Verification) ---
            subject = "Verify your email - ExtraPaints"
            context = {
                'user_name': user.full_name or user.username,
                'verify_url': verify_url,
                'site_name': 'ExtraPaints',
            }
            html_content = render_to_string('accounts/verification_email_html.html', context)
            plain_message = f"Hi {context['user_name']},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you!"
            # ----------------------------------------

            try:
                msg = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                messages.info(request, "Account created! Please check your email for a verification link.")
            except Exception as e:
                print(f"Registration email error: {e}")
                messages.error(request, "Account created, but verification email failed to send. Please try to resend.")

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
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    """
    Displays the user's profile information, saved ideas, saved portfolios,
    and order history.
    """
    saved_ideas = SavedIdea.objects.filter(user=request.user).select_related('idea')

    context = {
        'saved_ideas': saved_ideas,
    }
    return render(request, 'accounts/profile.html', context)


def verification_pending(request):
    return render(request, 'accounts/verification_pending.html')
