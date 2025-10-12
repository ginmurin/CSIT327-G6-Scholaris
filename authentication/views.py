from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import RegisterForm, LoginForm, ProfileForm, ForgotPasswordForm, ResetPasswordForm, ChangeEmailForm, ChangePasswordForm
from .models import User as AppUser
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import secrets

def landing_view(request):
    return render(request, "authentication/landing.html")

class RegisterView(View):
    template_name = "authentication/register.html"

    def get(self, request):
        if request.session.get("app_user_id"):
            return redirect("home")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # US 1.3.4: Automatically log in the user after successful registration
            request.session["app_user_id"] = user.id
            request.session["app_user_name"] = user.name
            request.session["app_user_timezone"] = user.timezone
            request.session["app_user_language"] = user.language
            
            return redirect("home")
        
        return render(request, self.template_name, {"form": form})

class LoginView(View):
    template_name = "authentication/login.html"

    def get(self, request):
        if request.session.get("app_user_id"):
            return redirect("home")
        return render(request, self.template_name, {"form": LoginForm()})
    
    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            
            # Update last_login timestamp
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Set session variables
            request.session["app_user_id"] = user.id
            request.session["app_user_name"] = user.name
            request.session["app_user_timezone"] = user.timezone
            request.session["app_user_language"] = user.language
            return redirect("home")
        return render(request, self.template_name, {"form": form})
    
@never_cache
def logout_view(request):
    request.session.flush()
    return redirect("login")


def require_login(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get("app_user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


@never_cache
@require_login
def profile_view(request):
    user_id = request.session.get("app_user_id")
    user = get_object_or_404(AppUser, id=user_id)
    
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Handle profile picture upload
            profile_picture_file = request.FILES.get('profile_picture')
            if profile_picture_file:
                upload_dir = 'profile_pictures'
                ext = profile_picture_file.name.split('.')[-1]
                filename = f"user_{user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                filepath = os.path.join(upload_dir, filename)
                path = default_storage.save(filepath, ContentFile(profile_picture_file.read()))
                user.profile_picture = path
            
            # Save all form fields
            user.name = form.cleaned_data['name']
            user.learningstyle = form.cleaned_data['learningstyle']
            user.goals = form.cleaned_data['goals']
            user.timezone = form.cleaned_data.get('timezone', 'UTC')
            user.language = form.cleaned_data.get('language', 'en')
            user.save()
            
            if user.name != request.session.get("app_user_name"):
                request.session["app_user_name"] = user.name
            
            request.session["app_user_timezone"] = user.timezone
            request.session["app_user_language"] = user.language
            
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
        else:
            if 'profile_picture' in form.errors:
                messages.error(request, form.errors['profile_picture'][0])
    else:
        form = ProfileForm(instance=user)
    
    return render(request, "authentication/profile.html", {
        "form": form,
        "user": user
    })


class ForgotPasswordView(View):
    template_name = "authentication/forgot_password.html"

    def get(self, request):
        if request.session.get("app_user_id"):
            return redirect("home")
        return render(request, self.template_name, {"form": ForgotPasswordForm()})

    def post(self, request):
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = AppUser.objects.get(email=email)
                
                # Generate secure reset token
                token = secrets.token_urlsafe(32)
                user.reset_token = token
                user.reset_token_created_at = timezone.now()
                user.save(update_fields=['reset_token', 'reset_token_created_at'])
                
                # Redirect directly to reset password page
                return redirect('reset_password', token=token)
                    
            except AppUser.DoesNotExist:
                # Don't reveal if email exists or not
                messages.error(request, "Email address not found.")
            
            return redirect('forgot_password')
        
        return render(request, self.template_name, {"form": form})


class ResetPasswordView(View):
    template_name = "authentication/reset_password.html"

    def get(self, request, token):
        if request.session.get("app_user_id"):
            return redirect("home")
        
        # Verify token exists and is not expired
        try:
            user = AppUser.objects.get(reset_token=token)
            
            # Check if token is expired (1 hour)
            if user.reset_token_created_at:
                time_diff = timezone.now() - user.reset_token_created_at
                if time_diff.total_seconds() > 3600:  # 1 hour
                    messages.error(request, "Reset link has expired. Please request a new one.")
                    return redirect('forgot_password')
            
            return render(request, self.template_name, {
                "form": ResetPasswordForm(),
                "token": token
            })
        except AppUser.DoesNotExist:
            messages.error(request, "Invalid reset link.")
            return redirect('forgot_password')

    def post(self, request, token):
        try:
            user = AppUser.objects.get(reset_token=token)
            
            # Check if token is expired
            if user.reset_token_created_at:
                time_diff = timezone.now() - user.reset_token_created_at
                if time_diff.total_seconds() > 3600:
                    messages.error(request, "Reset link has expired. Please request a new one.")
                    return redirect('forgot_password')
            
            form = ResetPasswordForm(request.POST)
            if form.is_valid():
                # Save new password (plain text)
                new_password = form.cleaned_data['password1']
                user.password = new_password
                user.reset_token = None
                user.reset_token_created_at = None
                user.save(update_fields=['password', 'reset_token', 'reset_token_created_at'])
                
                messages.success(request, "Password reset successful! You can now login with your new password.")
                return redirect('login')
            
            return render(request, self.template_name, {
                "form": form,
                "token": token
            })
            
        except AppUser.DoesNotExist:
            messages.error(request, "Invalid reset link.")
            return redirect('forgot_password')


@never_cache
@require_login
def change_email_view(request):
    user_id = request.session.get("app_user_id")
    user = get_object_or_404(AppUser, id=user_id)
    
    if request.method == "POST":
        form = ChangeEmailForm(request.POST, user=user)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            user.email = new_email
            user.save(update_fields=['email'])
            
            messages.success(request, "Email address updated successfully!")
            return redirect("profile")
    else:
        form = ChangeEmailForm(user=user)
    
    return render(request, "authentication/change_email.html", {
        "form": form,
        "user": user
    })


@never_cache
@require_login
def change_password_view(request):
    user_id = request.session.get("app_user_id")
    user = get_object_or_404(AppUser, id=user_id)
    
    if request.method == "POST":
        form = ChangePasswordForm(request.POST, user=user)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            user.password = new_password
            user.save(update_fields=['password'])
            
            messages.success(request, "Password changed successfully!")
            return redirect("profile")
    else:
        form = ChangePasswordForm(user=user)
    
    return render(request, "authentication/change_password.html", {
        "form": form,
        "user": user
    })
