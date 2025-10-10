from django.db import models
from authentication.models import User

# Create your models here.

class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    learning_objective = models.CharField(max_length=500)
    start_date = models.DateField()
    end_date = models.DateField()
    preferred_resources = models.CharField(max_length=300, blank=True, null=True, help_text="e.g., Books, Videos, Online Courses")
    estimated_hours_per_week = models.IntegerField(help_text="Estimated hours per week")
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_created']
    
    def __str__(self):
        return f"{self.title} - {self.user.name}"
