from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .. import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("google/", views.GoogleLoginView.as_view(), name="auth-google"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("password/forgot/", views.ForgotPasswordView.as_view(), name="auth-password-forgot"),
    path("password/verify/", views.VerifyResetCodeView.as_view(), name="auth-password-verify"),
    path("password/reset/", views.ResetPasswordView.as_view(), name="auth-password-reset"),
    path("password/change/", views.ChangePasswordView.as_view(), name="auth-password-change"),
]
