from django.urls import path
from .views import (
    RegisterView, LoginView, logout_view, landing_view, profile_view,
    ForgotPasswordView, ResetPasswordView, change_email_view, change_password_view
)

urlpatterns = [
    path("",                      landing_view,                name="landing"),
    path("register/",             RegisterView.as_view(),      name="register"),
    path("login/",                LoginView.as_view(),         name="login"),
    path("logout/",               logout_view,                 name="logout"),
    path("profile/",              profile_view,                name="profile"),
    path("forgot-password/",      ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/<str:token>/", ResetPasswordView.as_view(), name="reset_password"),
    path("change-email/",         change_email_view,           name="change_email"),
    path("change-password/",      change_password_view,        name="change_password"),
]