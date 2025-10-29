from django.contrib import admin
from .models import Quiz, Question, QuestionOption, QuizAttempt, Answer, QuizGrade


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    max_num = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'difficulty', 'status', 'total_questions', 'created_at']
    list_filter = ['status', 'difficulty', 'created_at']
    search_fields = ['title', 'description']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'order', 'points']
    list_filter = ['quiz']
    search_fields = ['question_text']
    inlines = [QuestionOptionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'percentage_score', 'is_passed', 'attempt_number', 'started_at']
    list_filter = ['is_passed', 'started_at']
    search_fields = ['user__name', 'quiz__title']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'answered_at']


@admin.register(QuizGrade)
class QuizGradeAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'score', 'graded_by', 'graded_at']
    list_filter = ['graded_at']
