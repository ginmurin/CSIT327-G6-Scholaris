from django.db import models

# Create your models here.
# authentication/models.py
from django.conf import settings
from django.db import models

class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, db_index=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=50, blank=True)
    learningstyle = models.CharField(max_length=50, blank=True)
    goals = models.TextField(blank=True)           # Goals

    class Meta:
        db_table = "users"   # will create/use public.users

    def __str__(self):
        return f"{self.name} <{self.email}>"