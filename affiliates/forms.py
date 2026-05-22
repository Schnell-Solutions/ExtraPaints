from django import forms

from .models import Affiliate


class AffiliateAdminForm(forms.ModelForm):
    """Partner details only — referral code is generated automatically on save."""

    class Meta:
        model = Affiliate
        fields = ('name', 'email', 'phone', 'is_active', 'notes')
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. Sarah Okello',
                'autocomplete': 'organization',
            }),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
