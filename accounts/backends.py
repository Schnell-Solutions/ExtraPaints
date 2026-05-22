from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with username or email (case-insensitive email)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        login = (username or kwargs.get('username') or '').strip()
        pwd = password or kwargs.get('password')
        if not login or not pwd:
            return None

        if '@' in login:
            user = User.objects.filter(email__iexact=login).first()
        else:
            user = User.objects.filter(username__iexact=login).first()

        if user and user.check_password(pwd) and self.user_can_authenticate(user):
            return user
        return None
