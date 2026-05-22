from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    SetPasswordForm,
)
from django.contrib.auth.password_validation import validate_password

from .models import User

AUTH_INPUT_CLASS = (
    'ep-input ep-auth-input block w-full rounded-md border border-gray-300 '
    'px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 '
    'focus:border-primary-900 focus:outline-none focus:ring-1 focus:ring-primary-900'
)


def _minimal_auth_fields(form):
    """Placeholder-only auth UI: hide labels and Django help text."""
    for field in form.fields.values():
        if field.label and field.widget.input_type != 'checkbox':
            field.label = ''
        field.help_text = ''
AUTH_CHECKBOX_CLASS = (
    'mt-0.5 h-4 w-4 shrink-0 rounded border-gray-300 text-primary-900 focus:ring-primary-900'
)


class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': AUTH_INPUT_CLASS, 'placeholder': 'Full name', 'autocomplete': 'name'}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': AUTH_INPUT_CLASS, 'placeholder': 'Email address', 'autocomplete': 'email'}),
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': AUTH_INPUT_CLASS, 'placeholder': 'Phone (optional)', 'autocomplete': 'tel'}),
    )
    accept_terms = forms.BooleanField(
        required=True,
        label='',
        error_messages={'required': 'You must accept the Terms and Privacy Policy to register.'},
        widget=forms.CheckboxInput(attrs={'class': AUTH_CHECKBOX_CLASS}),
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _minimal_auth_fields(self)
        for name in ('username', 'password1', 'password2'):
            if name in self.fields:
                placeholder = {
                    'username': 'Username',
                    'password1': 'Password',
                    'password2': 'Confirm password',
                }.get(name, '')
                self.fields[name].widget.attrs.update({
                    'class': AUTH_INPUT_CLASS,
                    'placeholder': placeholder,
                })
                if name == 'username':
                    self.fields[name].widget.attrs['autocomplete'] = 'username'
                elif name == 'password1':
                    self.fields[name].widget.attrs['autocomplete'] = 'new-password'
                else:
                    self.fields[name].widget.attrs['autocomplete'] = 'new-password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.phone = self.cleaned_data.get('phone') or ''
        user.is_active = False
        user.is_email_verified = False
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _minimal_auth_fields(self)
        self.fields['username'].widget.attrs.update({
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Username or email',
            'autofocus': True,
            'autocomplete': 'username',
        })
        self.fields['password'].widget.attrs.update({
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })


class OTPCodeForm(forms.Form):
    code = forms.CharField(
        label='',
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'ep-auth-otp-input ep-input ep-auth-input w-full tracking-[0.35em] font-mono text-lg',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
        }),
    )

    def clean_code(self):
        code = ''.join(ch for ch in self.cleaned_data.get('code', '') if ch.isdigit())
        if len(code) != 6:
            raise forms.ValidationError('Enter the 6-digit code from your email.')
        return code


class ResendEmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Email address',
            'autocomplete': 'email',
        }),
    )


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Email address',
            'autocomplete': 'email',
        }),
    )


class PasswordResetCompleteForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'new_password1': 'New password',
            'new_password2': 'Confirm password',
        }
        for name, field in self.fields.items():
            field.label = ''
            field.help_text = ''
            field.widget.attrs.update({
                'class': AUTH_INPUT_CLASS,
                'placeholder': placeholders.get(name, name),
                'autocomplete': 'new-password',
            })


class PasswordChangeStartForm(forms.Form):
    old_password = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Current password',
            'autocomplete': 'current-password',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        password = self.cleaned_data.get('old_password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Your current password is incorrect.')
        return password


class PasswordChangeCompleteForm(forms.Form):
    code = forms.CharField(
        label='',
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'ep-auth-otp-input ep-input ep-auth-input w-full tracking-[0.35em] font-mono text-lg',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'maxlength': '6',
        }),
    )
    new_password1 = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'New password',
            'autocomplete': 'new-password',
        }),
    )
    new_password2 = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        _minimal_auth_fields(self)

    def clean_code(self):
        code = ''.join(ch for ch in self.cleaned_data.get('code', '') if ch.isdigit())
        if len(code) != 6:
            raise forms.ValidationError('Enter the 6-digit code from your email.')
        return code

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', 'The two password fields did not match.')
        if p1:
            validate_password(p1, self.user)
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data['new_password1'])
        self.user.save(update_fields=['password'])
        return self.user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                'class',
                'block w-full rounded-md border border-gray-300 px-3 py-2.5 text-sm '
                'focus:border-primary-900 focus:outline-none focus:ring-1 focus:ring-primary-900',
            )


class AccountDeletionRequestForm(forms.Form):
    """Multi-step confirmation before submitting an account deletion request."""

    understand = forms.BooleanField(
        required=True,
        label='I understand my account will be deactivated and data removed.',
        error_messages={'required': 'Please confirm that you understand the consequences.'},
        widget=forms.CheckboxInput(attrs={'class': AUTH_CHECKBOX_CLASS}),
    )
    confirm_email = forms.EmailField(
        label='',
        widget=forms.EmailInput(attrs={
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Confirm account email',
            'autocomplete': 'email',
        }),
    )
    confirm_phrase = forms.CharField(
        label='',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': AUTH_INPUT_CLASS + ' font-mono uppercase',
            'autocomplete': 'off',
            'placeholder': 'Type DELETE',
        }),
    )
    password = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': AUTH_INPUT_CLASS,
            'placeholder': 'Current password',
            'autocomplete': 'current-password',
        }),
    )
    reason = forms.CharField(
        required=False,
        label='',
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': AUTH_INPUT_CLASS,
            'rows': 3,
            'placeholder': 'Reason (optional)',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        _minimal_auth_fields(self)

    def clean_confirm_email(self):
        email = self.cleaned_data.get('confirm_email', '').strip().lower()
        if email != (self.user.email or '').strip().lower():
            raise forms.ValidationError('Email does not match your account.')
        return email

    def clean_confirm_phrase(self):
        phrase = (self.cleaned_data.get('confirm_phrase') or '').strip().upper()
        if phrase != 'DELETE':
            raise forms.ValidationError('Please type DELETE exactly as shown.')
        return phrase

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Incorrect password.')
        return password
