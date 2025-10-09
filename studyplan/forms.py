from django import forms
from .models import StudyPlan

class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ['title', 'description', 'learning_objective', 'start_date', 'end_date', 'preferred_resources', 'estimated_hours_per_week']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Python Programming Fundamentals',
                'class': 'form-input'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Briefly describe your study plan...',
                'rows': 4,
                'class': 'form-input'
            }),
            'learning_objective': forms.TextInput(attrs={
                'placeholder': 'e.g., Master Python basics and build a web application',
                'class': 'form-input'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'preferred_resources': forms.TextInput(attrs={
                'placeholder': 'e.g., Books, Videos, Online Courses, Tutorials',
                'class': 'form-input'
            }),
            'estimated_hours_per_week': forms.NumberInput(attrs={
                'placeholder': 'Hours per week',
                'min': 1,
                'max': 168,
                'class': 'form-input'
            }),
        }
        labels = {
            'title': 'Study Plan Title',
            'description': 'Description',
            'learning_objective': 'Learning Objective',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'preferred_resources': 'Preferred Resources',
            'estimated_hours_per_week': 'Hours per Week',
        }
