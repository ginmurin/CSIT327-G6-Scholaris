from django.urls import path
from . import views

app_name = "admin_page"

urlpatterns = [
    path("home/", views.home, name="home"),
]
