from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone', 'password1', 'password2']


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)

class UserUpdateForm(forms.ModelForm):
    # Only include fields the user is allowed to edit from the profile page
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone']

