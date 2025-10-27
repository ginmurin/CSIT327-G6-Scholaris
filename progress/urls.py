from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    path('', views.progress_dashboard, name='dashboard'),
    path('plan/<int:plan_id>/', views.study_plan_progress, name='study_plan_detail'),
    path('achievements/', views.achievements_view, name='achievements'),
    
    # AJAX endpoints
    path('resource/<int:resource_progress_id>/toggle/', views.toggle_resource_completion, name='toggle_completion'),
    path('resource/<int:resource_progress_id>/update/', views.update_resource_progress, name='update_progress'),
    path('session/start/<int:plan_id>/', views.start_study_session, name='start_session'),
    path('session/end/<int:session_id>/', views.end_study_session, name='end_session'),
]
