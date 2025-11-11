from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from datetime import date, timedelta, datetime
from django.utils import timezone

class User(models.Model):
    id = models.BigAutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, db_index=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=50, blank=True, default="student")
    goals = models.TextField(default="To be determined")
    profile_picture = models.CharField(max_length=255, blank=True, null=True)
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_created_at = models.DateTimeField(blank=True, null=True)
    
    # Streak and Time Tracking
    last_login_date = models.DateField(blank=True, null=True)  # Last login date (for streak)
    login_streak = models.IntegerField(default=0)  # Current consecutive login days
    total_app_time = models.IntegerField(default=0)  # Total minutes spent on app
    session_start = models.DateTimeField(blank=True, null=True)  # Current session start time

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.name} <{self.email}>"
    
    def update_login_streak(self):
        """
        Update login streak based on last login date.
        +1 if logged in today, continue if yesterday, reset to 1 otherwise.
        """
        today = date.today()
        
        if self.last_login_date == today:
            # Already logged in today, no change
            return self.login_streak
        elif self.last_login_date == today - timedelta(days=1):
            # Logged in yesterday, continue streak
            self.login_streak += 1
        else:
            # Broke streak or first login
            self.login_streak = 1
        
        self.last_login_date = today
        return self.login_streak
    
    def start_session(self):
        """Mark the start of a session."""
        self.session_start = timezone.now()
    
    def end_session(self):
        """
        Calculate session duration and add to total app time.
        Returns minutes spent in this session.
        """
        if not self.session_start:
            return 0
        
        duration = timezone.now() - self.session_start
        minutes = int(duration.total_seconds() / 60)
        self.total_app_time += minutes
        self.session_start = None
        
        return minutes
    
    def get_app_time_formatted(self):
        """
        Returns total app time formatted as 'Xh Ym' (e.g., '2h 30m').
        """
        if not self.total_app_time:
            return "0m"
        
        hours = self.total_app_time // 60
        minutes = self.total_app_time % 60
        
        if hours == 0:
            return f"{minutes}m"
        elif minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {minutes}m"