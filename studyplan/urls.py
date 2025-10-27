from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_study_plans, name='list_study_plans'),
    path('create/', views.create_study_plan, name='create_study_plan'),
    path('edit/<int:plan_id>/', views.edit_study_plan, name='edit_study_plan'),
    path('delete/<int:plan_id>/', views.delete_study_plan, name='delete_study_plan'),
    path('<int:plan_id>/progress/', views.study_plan_progress, name='study_plan_progress'),
    path('<int:plan_id>/resources/', views.get_resources, name='study_plan_resources'),
    path('<int:plan_id>/resources/<int:resource_id>/toggle/', views.toggle_resource_completion, name='toggle_resource_completion'),
]
