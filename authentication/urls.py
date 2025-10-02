from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import RegisterView

app_name = "authentication"  # optional namespacing

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
]