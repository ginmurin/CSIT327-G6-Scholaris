from django import forms
from .models import StudyPlan
from datetime import date

class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ['title', 'description', 'learning_objective', 'topic_category', 'start_date', 'end_date', 'preferred_resources', 'estimated_hours_per_week']
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
            'topic_category': forms.Select(attrs={
                'class': 'form-input form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'min': date.today().isoformat()
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'min': date.today().isoformat()
            }),
            'preferred_resources': forms.Select(attrs={
                'class': 'form-input form-select'
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
            'topic_category': 'Topic Category',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'preferred_resources': 'Preferred Resources',
            'estimated_hours_per_week': 'Hours per Week',
        }
    
    def clean_start_date(self):
        """Validate that start date is not in the past (only for new plans)"""
        start_date = self.cleaned_data.get('start_date')
        # Only validate for new plans, allow existing plans to keep their dates
        if not self.instance.pk and start_date and start_date < date.today():
            raise forms.ValidationError("Start date cannot be in the past. Please select today or a future date.")
        return start_date
    
    def clean_end_date(self):
        """Validate that end date is not in the past (only for new plans)"""
        end_date = self.cleaned_data.get('end_date')
        # Only validate for new plans, allow existing plans to keep their dates
        if not self.instance.pk and end_date and end_date < date.today():
            raise forms.ValidationError("End date cannot be in the past. Please select today or a future date.")
        return end_date
    
    def clean(self):
        """Validate that end date is after start date"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data

