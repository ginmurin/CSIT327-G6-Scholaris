from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings

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

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.name} <{self.email}>"