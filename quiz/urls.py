from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz_list, name='quiz_list'),
    path('stats/', views.quiz_stats, name='quiz_stats'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('<int:quiz_id>/add-question-custom/', views.add_question_custom, name='add_question_custom'),
    path('<int:quiz_id>/publish/', views.publish_quiz, name='publish_quiz'),
    path('<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('attempt/<int:attempt_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('attempt/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
]
