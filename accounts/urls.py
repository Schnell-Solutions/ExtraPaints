from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/delete/', views.request_account_deletion, name='request_account_deletion'),
    path('profile/delete/submitted/', views.account_deletion_submitted, name='account_deletion_submitted'),

    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/new/', views.password_reset_set, name='password_reset_set'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        views.password_reset_confirm,
        name='password_reset_confirm',
    ),

    path('verify-email/', views.verify_email_otp, name='verify_email_otp'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
]
