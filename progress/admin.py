from django.contrib import admin
from .models import Progress, ResourceProgress, StudySession, Achievement

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['study_plan', 'user', 'completion_percentage', 'completed_resources', 'total_resources', 'total_hours_spent', 'last_activity']
    list_filter = ['user', 'started_at', 'completed_at']
    search_fields = ['study_plan__title', 'user__name', 'user__email']
    readonly_fields = ['started_at', 'last_activity', 'completed_at']
    ordering = ['-last_activity']

@admin.register(ResourceProgress)
class ResourceProgressAdmin(admin.ModelAdmin):
    list_display = ['study_plan_resource', 'user', 'progress_percentage', 'is_completed', 'time_spent', 'last_accessed']
    list_filter = ['is_completed', 'user', 'completed_at']
    search_fields = ['study_plan_resource__resource__title', 'user__name', 'user__email']
    readonly_fields = ['started_at', 'completed_at', 'last_accessed']
    ordering = ['-last_accessed']

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'study_plan', 'resource', 'started_at', 'ended_at', 'duration']
    list_filter = ['user', 'started_at', 'study_plan']
    search_fields = ['user__name', 'study_plan__title', 'resource__title']
    readonly_fields = ['started_at']
    ordering = ['-started_at']

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement_type', 'title', 'earned_at']
    list_filter = ['achievement_type', 'earned_at']
    search_fields = ['user__name', 'user__email', 'title']
    readonly_fields = ['earned_at']
    ordering = ['-earned_at']

