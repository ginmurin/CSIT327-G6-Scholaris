from django.db import models
from authentication.models import User
from studyplan.models import StudyPlan

class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_questions = models.IntegerField(default=0)
    passing_score = models.IntegerField(default=70, help_text="Passing score percentage")
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes")
    shuffle_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True)
    allow_retake = models.BooleanField(default=True)
    max_attempts = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quiz'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    order = models.IntegerField(default=0)
    points = models.IntegerField(default=1)
    explanation = models.TextField(blank=True, null=True, help_text="Explanation for the correct answer")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'question'
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'question_option'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.question} - Option {self.order}"


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_score = models.IntegerField(default=0)
    percentage_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_passed = models.BooleanField(default=False)
    time_taken = models.IntegerField(null=True, blank=True, help_text="Time taken in seconds")
    answers_count = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    attempt_number = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'quiz_attempt'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.quiz.title} (Attempt {self.attempt_number})"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, null=True, blank=True)
    answer_text = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'answer'
    
    def __str__(self):
        return f"{self.attempt} - {self.question}"


class QuizGrade(models.Model):
    attempt = models.OneToOneField(QuizAttempt, on_delete=models.CASCADE, related_name='grade')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(blank=True, null=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_quizzes')
    
    class Meta:
        db_table = 'quiz_grade'
    
    def __str__(self):
        return f"Grade for {self.attempt}"
