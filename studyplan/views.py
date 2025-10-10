from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import StudyPlan
from .forms import StudyPlanForm
from authentication.models import User

# Create your views here.

def require_login(view_func):
    """Custom decorator to check if user is logged in via session"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get("app_user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper

@require_login
def list_study_plans(request):
    """Display all study plans for the logged-in user"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plans = StudyPlan.objects.filter(user=user)
    return render(request, 'studyplan/list_study_plans.html', {
        'study_plans': study_plans,
        'name': request.session.get("app_user_name", "User")
    })

@require_login
def create_study_plan(request):
    """Create a new study plan"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        form = StudyPlanForm(request.POST)
        if form.is_valid():
            study_plan = form.save(commit=False)
            study_plan.user = user
            study_plan.save()
            messages.success(request, f'Study plan "{study_plan.title}" created successfully!')
            return redirect('list_study_plans')
    else:
        form = StudyPlanForm()
    
    return render(request, 'studyplan/create_study_plan.html', {
        'form': form,
        'name': request.session.get("app_user_name", "User")
    })

@require_login
def edit_study_plan(request, plan_id):
    """Edit an existing study plan"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
    
    if request.method == 'POST':
        form = StudyPlanForm(request.POST, instance=study_plan)
        if form.is_valid():
            form.save()
            messages.success(request, f'Study plan "{study_plan.title}" updated successfully!')
            return redirect('list_study_plans')
    else:
        form = StudyPlanForm(instance=study_plan)
    
    return render(request, 'studyplan/edit_study_plan.html', {
        'form': form,
        'study_plan': study_plan,
        'name': request.session.get("app_user_name", "User")
    })

@require_login
def delete_study_plan(request, plan_id):
    """Delete a study plan"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
    
    if request.method == 'POST':
        title = study_plan.title
        study_plan.delete()
        messages.success(request, f'Study plan "{title}" deleted successfully!')
        return redirect('list_study_plans')
    
    return render(request, 'studyplan/delete_confirm.html', {
        'study_plan': study_plan,
        'name': request.session.get("app_user_name", "User")
    })

