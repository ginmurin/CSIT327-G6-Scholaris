from django.urls import path
from . import views

app_name = "admin_page"

urlpatterns = [
    path("home/", views.home, name="home"),

    path("users/", views.users_list, name="users_list"),
    path("users/<int:user_id>/", views.user_detail, name="user_detail"),
    path("users/<int:user_id>/delete/", views.delete_user, name="delete_user"),

    path("plans/<int:plan_id>/open/", views.open_plan, name="open_plan"),

    path("users/<int:user_id>/view-as/", views.view_as_user, name="view_as_user"),
    path("return-admin/", views.return_to_admin, name="return_to_admin"),
]
