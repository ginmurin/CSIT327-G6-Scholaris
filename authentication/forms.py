from django import forms
from django.contrib.auth.hashers import make_password, check_password
from .models import User as AppUser

class RegisterForm(forms.Form):
    name = forms.CharField(
        max_length=150, 
        required=True,
        label="Name",
        widget=forms.TextInput(attrs={"placeholder": "Enter your full name"})
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Enter your email address"})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password (min. 8 characters)"}), 
        required=True,
        label="Password",
        min_length=8
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm your password"}), 
        required=True,
        label="Confirm Password"
    )
    role = forms.CharField(max_length=50, required=False, initial="student", label="Role")
    learningstyle = forms.ChoiceField(
        choices=[
            ('', 'Select Your Learning Style'),
            ('Visual', 'Visual - Learn through images, diagrams, and videos'),
            ('Auditory', 'Auditory - Learn through listening and discussions'),
            ('Kinesthetic', 'Kinesthetic - Learn through hands-on activities'),
            ('Reading/Writing', 'Reading/Writing - Learn through text and notes')
        ],
        required=True,
        label="Learning Style"
    )
    goals = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "What do you want to achieve? (e.g., Master Python, Pass exams, Learn web development)"}),
        required=True,
        label="Learning Goals"
    )

    def clean_name(self):
        """US 1.3.1: Validate name is provided"""
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name

    def clean_email(self):
        """US 1.3.1 & 1.3.2: Validate email and check for duplicates"""
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        
        # US 1.3.2: Check if email already registered
        if AppUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        
        return email
    
    def clean_password1(self):
        """US 1.3.3: Validate password security requirements"""
        password = self.cleaned_data.get("password1", "")
        
        # Minimum 8 characters
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        
        # Check if password contains at least one number
        if not any(char.isdigit() for char in password):
            raise forms.ValidationError("Password must contain at least one number.")
        
        # Check if password contains at least one letter
        if not any(char.isalpha() for char in password):
            raise forms.ValidationError("Password must contain at least one letter.")
        
        return password
    
    def clean_learningstyle(self):
        """Validate learning style is selected"""
        learningstyle = self.cleaned_data.get("learningstyle")
        if not learningstyle or learningstyle == '':
            raise forms.ValidationError("Please select your learning style.")
        return learningstyle
    
    def clean_goals(self):
        """Validate learning goals are provided"""
        goals = self.cleaned_data.get("goals", "").strip()
        if not goals:
            raise forms.ValidationError("Please describe your learning goals.")
        if len(goals) < 10:
            raise forms.ValidationError("Please provide more detail about your goals (at least 10 characters).")
        return goals

    def clean(self):
        """US 1.3.1 & 1.3.3: Validate password confirmation matches"""
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")
        
        return cleaned

    def save(self):
        """US 1.3.1: Create new user account in database"""
        d = self.cleaned_data
        return AppUser.objects.create(
            name=d["name"].strip(),
            email=d["email"].lower(),
            password=make_password(d["password1"]),  # Hash password securely
            role="student",
            learningstyle=d["learningstyle"],
            goals=d["goals"].strip(),
        )
    
class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        password = cleaned.get("password") or ""
        try:
            user = AppUser.objects.get(email=email)
        except AppUser.DoesNotExist:
            raise forms.ValidationError("Invalid email or password.")
        if not check_password(password, user.password):  # Compare hashed passwords securely
            raise forms.ValidationError("Invalid email or password.")
        cleaned["user"] = user
        return cleaned


class ProfileForm(forms.ModelForm):
    """
    US 1.4.1: Update user name
    US 1.4.2: Update timezone/language preferences
    US 1.4.3: Profile picture upload with size validation
    """
    
    profile_picture = forms.FileField(
        required=False,
        label="Profile Picture",
        help_text="Max file size: 5MB. Allowed formats: JPG, PNG, GIF",
        widget=forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/gif'})
    )
    
    learningstyle = forms.ChoiceField(
        choices=[
            ('Visual', 'Visual - Learn through images, diagrams, and videos'),
            ('Auditory', 'Auditory - Learn through listening and discussions'),
            ('Kinesthetic', 'Kinesthetic - Learn through hands-on activities'),
            ('Reading/Writing', 'Reading/Writing - Learn through text and notes')
        ],
        required=True,
        label="Learning Style"
    )
    
    timezone = forms.ChoiceField(
        choices=[
            ('UTC', 'UTC (Coordinated Universal Time)'),
            ('America/New_York', 'Eastern Time (US & Canada)'),
            ('America/Chicago', 'Central Time (US & Canada)'),
            ('America/Denver', 'Mountain Time (US & Canada)'),
            ('America/Los_Angeles', 'Pacific Time (US & Canada)'),
            ('Europe/London', 'London'),
            ('Europe/Paris', 'Paris/Berlin'),
            ('Asia/Tokyo', 'Tokyo'),
            ('Asia/Shanghai', 'Beijing/Shanghai'),
            ('Asia/Manila', 'Manila'),
            ('Australia/Sydney', 'Sydney'),
        ],
        required=False,
        label="Time Zone",
        initial='UTC'
    )
    
    language = forms.ChoiceField(
        choices=[
            ('en', 'English'),
            ('es', 'Español (Spanish)'),
            ('fr', 'Français (French)'),
            ('de', 'Deutsch (German)'),
            ('zh', '中文 (Chinese)'),
            ('ja', '日本語 (Japanese)'),
            ('ko', '한국어 (Korean)'),
            ('tl', 'Tagalog (Filipino)'),
        ],
        required=False,
        label="Language",
        initial='en'
    )
    
    class Meta:
        model = AppUser
        fields = ['name', 'learningstyle', 'goals', 'timezone', 'language']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
            'goals': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What do you want to achieve?'}),
        }
        labels = {
            'name': 'Full Name',
            'learningstyle': 'Learning Style',
            'goals': 'Learning Goals',
        }
    
    def clean_name(self):
        """US 1.4.1: Validate name update"""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Name cannot be empty.")
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name
    
    def clean_profile_picture(self):
        """US 1.4.3: Validate profile picture file size"""
        picture = self.cleaned_data.get('profile_picture')
        
        if picture:
            # Check file size (max 5MB)
            if picture.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError(
                    f"File size too large. Maximum allowed size is 5MB. "
                    f"Your file is {picture.size / (1024 * 1024):.2f}MB."
                )
            
            # Validate file extension
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            ext = picture.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    f"Invalid file type. Allowed formats: {', '.join(valid_extensions).upper()}"
                )
        
        return picture


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter your registered email",
            "class": "form-control"
        })
    )


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter new password (min. 8 characters)",
            "class": "form-control"
        }), 
        required=True,
        label="New Password",
        min_length=8
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm new password",
            "class": "form-control"
        }), 
        required=True,
        label="Confirm Password"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data


class ChangeEmailForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter your current password",
            "class": "form-control"
        }), 
        required=True,
        label="Current Password"
    )
    new_email = forms.EmailField(
        required=True,
        label="New Email Address",
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter new email address",
            "class": "form-control"
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if self.user and not check_password(password, self.user.password):
            raise forms.ValidationError("Current password is incorrect.")
        return password
    
    def clean_new_email(self):
        email = self.cleaned_data.get('new_email')
        if self.user and email == self.user.email:
            raise forms.ValidationError("New email must be different from current email.")
        if AppUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter your current password",
            "class": "form-control"
        }), 
        required=True,
        label="Current Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter new password (min. 8 characters)",
            "class": "form-control"
        }), 
        required=True,
        label="New Password",
        min_length=8
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm new password",
            "class": "form-control"
        }), 
        required=True,
        label="Confirm New Password"
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def clean_current_password(self):
        password = self.cleaned_data.get('current_password')
        if self.user and not check_password(password, self.user.password):
            raise forms.ValidationError("Current password is incorrect.")
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("New passwords do not match.")
        
        return cleaned_data
