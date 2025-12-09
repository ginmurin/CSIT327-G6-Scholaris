from django.contrib import admin
from .models import StudyPlan, Milestone, Resource, ProgressLog  # adjust to your real models


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "learning_style", "start_date", "end_date", "hours_per_week", "is_active")
    list_filter = ("learning_style", "is_active", "start_date")
    search_fields = ("title", "goal", "user__username")
    ordering = ("-start_date",)
    date_hierarchy = "start_date"
    list_per_page = 20


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("study_plan", "title", "due_date", "is_done")
    list_filter = ("is_done", "due_date")
    search_fields = ("title", "study_plan__title")
    ordering = ("due_date",)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("study_plan", "title", "resource_type", "learning_style", "url")
    list_filter = ("resource_type", "learning_style")
    search_fields = ("title", "study_plan__title")
    ordering = ("title",)


@admin.register(ProgressLog)
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ("study_plan", "log_date", "hours_spent", "notes_short")
    list_filter = ("log_date",)
    search_fields = ("study_plan__title", "notes")
    ordering = ("-log_date",)

    def notes_short(self, obj):
        return (obj.notes[:40] + "...") if obj.notes and len(obj.notes) > 40 else obj.notes
    notes_short.short_description = "Notes"
