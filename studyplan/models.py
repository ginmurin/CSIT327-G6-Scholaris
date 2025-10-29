from django.db import models
from authentication.models import User

class StudyPlan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    learning_objective = models.CharField(max_length=500)
    start_date = models.DateField()
    end_date = models.DateField()
    preferred_resources = models.CharField(max_length=300, blank=True, null=True, help_text="e.g., Books, Videos, Online Courses")
    estimated_hours_per_week = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_created']
        db_table = 'studyplan'
    
    def __str__(self):
        return f"{self.title} - {self.user.name}"

class StudyPlanResource(models.Model):
    study_plan = models.ForeignKey('StudyPlan', on_delete=models.CASCADE, related_name='plan_resources')
    resource = models.ForeignKey('resources.Resource', on_delete=models.CASCADE, related_name='study_plans')
    order_index = models.IntegerField(default=0)
    priority = models.IntegerField(default=0)  # Added to match database schema
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'studyplanresource'
        ordering = ['priority', 'order_index', 'id']
        unique_together = [['study_plan', 'resource']]
    
    def __str__(self):
        return f"{self.study_plan.title} - {self.resource.title}"
