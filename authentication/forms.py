from django import forms
from .models import User as AppUser

class RegisterForm(forms.Form):
    name = forms.CharField(max_length=150, label="Name")
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    role = forms.CharField(max_length=50, required=False, initial="student", label="Role")
    learningstyle = forms.CharField(max_length=50, required=False, label="Learning Style")
    goals = forms.CharField(widget=forms.Textarea(attrs={"rows":3}), required=False, label="Goals")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if AppUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self):
        d = self.cleaned_data
        return AppUser.objects.create(
            name=d["name"].strip(),
            email=d["email"].lower(),
            password=d["password1"],  # Store plain text password
            role="student",
            learningstyle=(d.get("learningstyle") or "").strip() or None,
            goals=(d.get("goals") or "").strip() or None,
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
        if password != user.password:  # Compare plain text passwords
            raise forms.ValidationError("Invalid email or password.")
        cleaned["user"] = user
        return cleaned