from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.forms import AccountDeletionRequestForm, UserRegisterForm
from accounts.models import AccountDeletionRequest, AuthOTP
from accounts.services.otp import create_otp, verify_otp

User = get_user_model()


class OTPServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='otpuser',
            email='otp@example.com',
            password='SecurePass123!',
        )

    def test_verify_valid_code(self):
        code = create_otp(self.user, AuthOTP.Purpose.EMAIL_VERIFY)
        ok, err = verify_otp(self.user, AuthOTP.Purpose.EMAIL_VERIFY, code)
        self.assertTrue(ok)
        self.assertEqual(err, '')

    def test_reject_invalid_code(self):
        create_otp(self.user, AuthOTP.Purpose.EMAIL_VERIFY)
        ok, err = verify_otp(self.user, AuthOTP.Purpose.EMAIL_VERIFY, '000000')
        self.assertFalse(ok)
        self.assertTrue(err)


class RegistrationFormTests(TestCase):
    def test_requires_terms_acceptance(self):
        form = UserRegisterForm({
            'username': 'newuser',
            'full_name': 'New User',
            'email': 'new@example.com',
            'phone': '',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'accept_terms': False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('accept_terms', form.errors)


class EmailVerificationOTPViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='verifyme',
            email='verify@example.com',
            password='SecurePass123!',
            is_active=False,
            is_email_verified=False,
        )

    def test_verify_email_otp_activates_user(self):
        code = create_otp(self.user, AuthOTP.Purpose.EMAIL_VERIFY)
        session = self.client.session
        session['auth_verify_user_id'] = self.user.pk
        session.save()

        response = self.client.post(
            reverse('verify_email_otp'),
            {'code': code},
        )
        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_active)


class AccountDeletionFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='deleteuser',
            email='delete@example.com',
            password='SecurePass123!',
            full_name='Delete User',
            is_email_verified=True,
            is_active=True,
        )

    def test_requires_delete_phrase_and_password(self):
        form = AccountDeletionRequestForm(
            self.user,
            {
                'understand': True,
                'confirm_email': 'delete@example.com',
                'confirm_phrase': 'WRONG',
                'password': 'SecurePass123!',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_phrase', form.errors)

    def test_deletion_request_deactivates_user(self):
        self.client.login(username='deleteuser', password='SecurePass123!')
        response = self.client.post(
            reverse('request_account_deletion'),
            {
                'understand': True,
                'confirm_email': 'delete@example.com',
                'confirm_phrase': 'DELETE',
                'password': 'SecurePass123!',
                'reason': 'No longer needed',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(AccountDeletionRequest.objects.filter(
            email_snapshot='delete@example.com',
            status=AccountDeletionRequest.Status.PENDING,
        ).count(), 1)


class ProfileAccessTests(TestCase):
    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
