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
    
    CATEGORY_CHOICES = [
        ('programming', 'Programming'),
        ('web_development', 'Web Development'),
        ('data_science', 'Data Science'),
        ('machine_learning', 'Machine Learning'),
        ('mobile_development', 'Mobile Development'),
        ('design', 'Design'),
        ('business', 'Business'),
        ('languages', 'Languages'),
        ('science', 'Science'),
        ('arts', 'Arts & Music'),
        ('cooking', 'Cooking'),
        ('fitness', 'Fitness'),
        ('other', 'Other'),
    ]
    
    topic = models.CharField(max_length=200, db_index=True)
    title = models.CharField(max_length=300)
    url = models.URLField(max_length=500, unique=True)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', db_index=True)
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='all')
    platform = models.CharField(max_length=100)
    learning_style = models.CharField(max_length=200, blank=True)
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
            models.Index(fields=['category', 'learning_style']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.platform}) - {self.topic}"
    
    def increment_recommendation_count(self):
        self.times_recommended += 1
        self.save(update_fields=['times_recommended'])
    
    @staticmethod
    def detect_category_from_topic(topic):
        """Detect category from topic keywords"""
        topic_lower = topic.lower()
        
        # Programming keywords
        if any(word in topic_lower for word in ['python', 'java', 'javascript', 'c++', 'c#', 'programming', 'coding', 'algorithm', 'data structures']):
            return 'programming'
        
        # Web development
        if any(word in topic_lower for word in ['web', 'html', 'css', 'react', 'vue', 'angular', 'django', 'flask', 'node', 'frontend', 'backend']):
            return 'web_development'
        
        # Data science
        if any(word in topic_lower for word in ['data science', 'data analysis', 'pandas', 'numpy', 'statistics', 'analytics']):
            return 'data_science'
        
        # Machine learning
        if any(word in topic_lower for word in ['machine learning', 'ml', 'ai', 'artificial intelligence', 'neural', 'deep learning', 'tensorflow', 'pytorch']):
            return 'machine_learning'
        
        # Mobile development
        if any(word in topic_lower for word in ['mobile', 'android', 'ios', 'swift', 'kotlin', 'react native', 'flutter']):
            return 'mobile_development'
        
        # Design
        if any(word in topic_lower for word in ['design', 'ui', 'ux', 'photoshop', 'illustrator', 'figma', 'drawing', 'art']):
            return 'design'
        
        # Business
        if any(word in topic_lower for word in ['business', 'marketing', 'management', 'entrepreneurship', 'startup']):
            return 'business'
        
        # Languages
        if any(word in topic_lower for word in ['language', 'english', 'spanish', 'french', 'german', 'japanese', 'chinese', 'learn to speak']):
            return 'languages'
        
        # Science
        if any(word in topic_lower for word in ['science', 'physics', 'chemistry', 'biology', 'math', 'mathematics']):
            return 'science'
        
        # Arts & Music
        if any(word in topic_lower for word in ['music', 'guitar', 'piano', 'singing', 'painting', 'arts', 'craft']):
            return 'arts'
        
        # Cooking
        if any(word in topic_lower for word in ['cooking', 'baking', 'recipe', 'culinary', 'chef']):
            return 'cooking'
        
        # Fitness
        if any(word in topic_lower for word in ['fitness', 'workout', 'exercise', 'yoga', 'gym', 'health']):
            return 'fitness'
        
        # Default
        return 'other'
