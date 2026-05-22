from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in
        from core.services.guest_merge import merge_guest_saves_into_user

        def _merge_guest_saves(sender, request, user, **kwargs):
            merge_guest_saves_into_user(request, user)

        user_logged_in.connect(_merge_guest_saves, dispatch_uid='extrapaints_merge_guest_saves')
