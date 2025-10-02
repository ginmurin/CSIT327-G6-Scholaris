from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    name = request.session.get("app_user_name")
    return HttpResponse(f"Welcome{', ' + name if name else ''}!")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("", include("authentication.urls")),
]
