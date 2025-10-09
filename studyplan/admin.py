from django.contrib import admin
from .models import StudyPlan

# Register your models here.

@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'learning_objective', 'start_date', 'end_date', 'estimated_hours_per_week', 'date_created')
    list_filter = ('start_date', 'end_date', 'date_created')
    search_fields = ('title', 'learning_objective', 'user__name', 'user__email')
    date_hierarchy = 'date_created'
    ordering = ('-date_created',)
    readonly_fields = ('date_created', 'date_modified')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'learning_objective', 'description')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'estimated_hours_per_week')
        }),
        ('Resources', {
            'fields': ('preferred_resources',)
        }),
        ('Timestamps', {
            'fields': ('date_created', 'date_modified'),
            'classes': ('collapse',)
        }),
    )

