from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

@never_cache
def home(request):
    if not request.session.get("app_user_id"):
        return redirect("login")
    return render(request, "authentication/home.html",
                  {"name": request.session.get("app_user_name") or "User"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("home/", home),
    path("", include("authentication.urls")),
]
