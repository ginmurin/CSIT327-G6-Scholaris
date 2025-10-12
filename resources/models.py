from django.db import models

class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('practice', 'Practice/Interactive'),
        ('course', 'Online Course'),
        ('documentation', 'Documentation'),
        ('tutorial', 'Tutorial'),
        ('book', 'Book/E-book'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    
    topic = models.CharField(max_length=200, db_index=True)
    title = models.CharField(max_length=300)
    url = models.URLField(max_length=500, unique=True)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, db_index=True)
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='all')
    platform = models.CharField(max_length=100)
    learning_style = models.CharField(max_length=50, blank=True)
    estimated_time = models.CharField(max_length=50, blank=True)
    is_external = models.BooleanField(default=True)
    is_free = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    times_recommended = models.IntegerField(default=0)
    
    class Meta:
        db_table = "resources"
        ordering = ['-times_recommended', '-created_at']
        indexes = [
            models.Index(fields=['topic', 'resource_type']),
            models.Index(fields=['topic', 'learning_style']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.platform}) - {self.topic}"
    
    def increment_recommendation_count(self):
        self.times_recommended += 1
        self.save(update_fields=['times_recommended'])
