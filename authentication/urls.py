from django.urls import path
from .views import RegisterView, LoginView, logout_view, landing_view

urlpatterns = [
    path("",          landing_view,            name="landing"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/",    LoginView.as_view(),    name="login"),
    path("logout/",   logout_view,            name="logout"),
]