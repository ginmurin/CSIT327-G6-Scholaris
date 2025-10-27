from django.db import models
from django.utils import timezone
from authentication.models import User
from studyplan.models import StudyPlan, StudyPlanResource

class Progress(models.Model):
    """Track overall progress for a study plan"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_records')
    study_plan = models.OneToOneField(StudyPlan, on_delete=models.CASCADE, related_name='progress')
    total_resources = models.IntegerField(default=0)
    completed_resources = models.IntegerField(default=0)
    total_hours_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    started_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'progress'
        verbose_name_plural = 'Progress'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Progress: {self.study_plan.title} - {self.completion_percentage}%"
    
    def update_progress(self):
        """Recalculate progress metrics"""
        resources = self.study_plan.plan_resources.all()
        self.total_resources = resources.count()
        self.completed_resources = resources.filter(is_completed=True).count()
        
        if self.total_resources > 0:
            self.completion_percentage = (self.completed_resources / self.total_resources) * 100
        else:
            self.completion_percentage = 0
        
        # Mark as completed if all resources are done
        if self.total_resources > 0 and self.completed_resources == self.total_resources:
            if not self.completed_at:
                self.completed_at = timezone.now()
                self.study_plan.status = 'completed'
                self.study_plan.save(update_fields=['status'])
        
        # Set started_at if not set and has activity
        if not self.started_at and self.completed_resources > 0:
            self.started_at = timezone.now()
        
        self.save()

class ResourceProgress(models.Model):
    """Track progress for individual resources within a study plan"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_progress')
    study_plan_resource = models.OneToOneField(StudyPlanResource, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    time_spent = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Hours spent on this resource")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True, help_text="Personal notes about this resource")
    
    class Meta:
        db_table = 'resource_progress'
        ordering = ['study_plan_resource__order_index']
        unique_together = [['user', 'study_plan_resource']]
    
    def __str__(self):
        return f"{self.study_plan_resource.resource.title} - {self.progress_percentage}%"
    
    def mark_completed(self):
        """Mark resource as completed"""
        self.is_completed = True
        self.progress_percentage = 100.00
        self.completed_at = timezone.now()
        
        # Also update the StudyPlanResource
        self.study_plan_resource.is_completed = True
        self.study_plan_resource.completion_date = timezone.now().date()
        self.study_plan_resource.save()
        
        self.save()
        
        # Update overall progress
        progress = Progress.objects.filter(
            user=self.user,
            study_plan=self.study_plan_resource.study_plan
        ).first()
        if progress:
            progress.update_progress()
    
    def mark_incomplete(self):
        """Mark resource as incomplete"""
        self.is_completed = False
        self.completed_at = None
        
        # Also update the StudyPlanResource
        self.study_plan_resource.is_completed = False
        self.study_plan_resource.completion_date = None
        self.study_plan_resource.save()
        
        self.save()
        
        # Update overall progress
        progress = Progress.objects.filter(
            user=self.user,
            study_plan=self.study_plan_resource.study_plan
        ).first()
        if progress:
            progress.update_progress()

class StudySession(models.Model):
    """Track individual study sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='study_sessions')
    resource = models.ForeignKey('resources.Resource', on_delete=models.SET_NULL, null=True, blank=True, related_name='study_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Session duration in hours")
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'study_session'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.study_plan.title} - {self.started_at.date()}"
    
    def end_session(self):
        """End the study session and calculate duration"""
        if not self.ended_at:
            self.ended_at = timezone.now()
            duration_seconds = (self.ended_at - self.started_at).total_seconds()
            self.duration = duration_seconds / 3600  # Convert to hours
            self.save()
            
            # Update progress total hours
            progress = Progress.objects.filter(
                user=self.user,
                study_plan=self.study_plan
            ).first()
            if progress:
                progress.total_hours_spent += self.duration
                progress.save()

class Achievement(models.Model):
    """User achievements and milestones"""
    ACHIEVEMENT_TYPES = [
        ('first_plan', 'Created First Study Plan'),
        ('first_completion', 'Completed First Resource'),
        ('plan_completed', 'Completed Study Plan'),
        ('streak_7', '7-Day Study Streak'),
        ('streak_30', '30-Day Study Streak'),
        ('hours_10', '10 Hours Studied'),
        ('hours_50', '50 Hours Studied'),
        ('hours_100', '100 Hours Studied'),
        ('resources_10', '10 Resources Completed'),
        ('resources_50', '50 Resources Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'achievement'
        ordering = ['-earned_at']
        unique_together = [['user', 'achievement_type']]
    
    def __str__(self):
        return f"{self.user.name} - {self.title}"
