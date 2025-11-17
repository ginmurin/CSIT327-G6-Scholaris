from django.urls import path
from . import views

urlpatterns = [
    path("notifications/", views.notification_history, name="notification_history"),
]
