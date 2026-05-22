from django import forms

_INPUT = 'w-full px-4 py-2 border border-gray-300 rounded focus:ring-primary-900 focus:border-primary-900 transition duration-150'


class HoneypotForm(forms.Form):
    """Base form with a hidden honeypot field (must subclass this, not a plain mixin)."""

    website = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'tabindex': '-1',
                'class': 'ep-honeypot',
            }
        ),
    )

    def clean_website(self):
        value = self.cleaned_data.get('website', '')
        if value and str(value).strip():
            raise forms.ValidationError('Invalid submission.')
        return ''


_REFERRAL = 'w-full px-4 py-2 border border-gray-300 rounded focus:ring-primary-900 focus:border-primary-900 uppercase tracking-wide'


class ContactForm(HoneypotForm):
    referral_code = forms.CharField(
        required=False,
        max_length=32,
        label='Referral Code (Optional)',
        widget=forms.TextInput(attrs={'class': _REFERRAL, 'placeholder': 'e.g. JOHN-M7K2'}),
    )
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': _INPUT}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': _INPUT}))
    phone = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TelInput(attrs={'class': _INPUT, 'placeholder': '+254...'}),
    )
    message = forms.CharField(widget=forms.Textarea(attrs={'class': _INPUT, 'rows': 5}))


class QuickInquiryForm(HoneypotForm):
    referral_code = forms.CharField(
        required=False,
        max_length=32,
        label='Referral Code (Optional)',
        widget=forms.TextInput(attrs={'class': 'ep-input uppercase tracking-wide', 'placeholder': 'e.g. JOHN-M7K2'}),
    )
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'ep-input'}))
    phone = forms.CharField(max_length=30, widget=forms.TelInput(attrs={'class': 'ep-input'}))
    project_reference = forms.CharField(
        max_length=255,
        required=False,
        label='Product or project',
        widget=forms.TextInput(attrs={'class': 'ep-input', 'placeholder': 'e.g. Exterior emulsion, 20L'}),
    )


class QuoteSubmitForm(HoneypotForm):
    referral_code = forms.CharField(
        required=False,
        max_length=32,
        label='Referral Code (Optional)',
    )
    name = forms.CharField(max_length=200)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30)
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
