from django.contrib import admin
from .models import Resource

# Register your models here.

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'resource_type', 'platform', 'difficulty', 'times_recommended', 'is_free', 'created_at')
    list_filter = ('resource_type', 'difficulty', 'is_free', 'platform')
    search_fields = ('title', 'topic', 'platform', 'description')
    readonly_fields = ('created_at', 'updated_at', 'times_recommended')
    ordering = ('-times_recommended', '-created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('topic', 'title', 'url', 'description')
        }),
        ('Classification', {
            'fields': ('resource_type', 'difficulty', 'platform')
        }),
        ('Additional Details', {
            'fields': ('estimated_time', 'is_free', 'language')
        }),
        ('Tracking', {
            'fields': ('times_recommended', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
