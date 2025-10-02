from django.shortcuts import render, redirect
from django.views import View
from .forms import RegisterForm

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
