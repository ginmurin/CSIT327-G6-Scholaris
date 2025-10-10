from django.shortcuts import render, redirect
from django.views import View
from .forms import RegisterForm, LoginForm
from django.views.decorators.cache import never_cache

def landing_view(request):
    """Public landing page - accessible to everyone"""
    return render(request, "authentication/landing.html")

class RegisterView(View):
    template_name = "authentication/register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            request.session["app_user_id"] = user.id
            request.session["app_user_name"] = user.name
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
            request.session["app_user_id"] = user.id
            request.session["app_user_name"] = user.name
            return redirect("home")
        return render(request, self.template_name, {"form": form})
    
@never_cache
def logout_view(request):
    request.session.flush()
    return redirect("login")