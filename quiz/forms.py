from django import forms
from .models import Quiz, Question, QuestionOption

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'study_plan', 'difficulty', 'passing_score', 
                  'time_limit', 'shuffle_questions', 'show_correct_answers', 'allow_retake', 'max_attempts', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quiz title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quiz description (optional)',
                'rows': 3
            }),
            'study_plan': forms.Select(attrs={
                'class': 'form-control'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-control'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'value': 70
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Time limit in minutes (optional)',
                'min': 1
            }),
            'shuffle_questions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_correct_answers': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_retake': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'max_attempts': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Maximum attempts (optional)',
                'min': 1
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class QuestionForm(forms.ModelForm):
    option_a = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option A'
        })
    )
    option_b = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option B'
        })
    )
    option_c = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option C'
        })
    )
    option_d = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Option D'
        })
    )
    correct_answer = forms.ChoiceField(
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = Question
        fields = ['question_text', 'explanation']
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your question',
                'rows': 3
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Explain why this is the correct answer (optional)',
                'rows': 2
            }),
        }
