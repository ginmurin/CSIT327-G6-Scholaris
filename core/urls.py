from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

@never_cache
def home(request):
    # Redirect to landing if not logged in
    if not request.session.get("app_user_id"):
        return redirect("landing")
    # Show authenticated home page
    return render(request, "authentication/home.html",
                  {"name": request.session.get("app_user_name") or "User"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("authentication.urls")),
    path("home/", home, name="home"),
    path("study-plans/", include("studyplan.urls")),
]
