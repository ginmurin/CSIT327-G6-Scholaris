from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import StudyPlan
from .forms import StudyPlanForm
from authentication.models import User
from core.ai_service import LearningAIService

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
    """Create a new study plan with AI recommendations"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    # Generate AI recommendations for creating study plans
    ai_recommendations = None
    ai_resources = None
    
    if request.method == 'POST':
        form = StudyPlanForm(request.POST)
        if form.is_valid():
            study_plan = form.save(commit=False)
            study_plan.user = user
            
            # Generate topic-specific AI recommendations
            try:
                topic_recommendations = LearningAIService.generate_study_recommendations(
                    learning_style=user.learningstyle,
                    goals=user.goals,
                    topic=study_plan.title  # Use the study plan title as topic
                )
                
                # Add AI insights to the description if user wants
                if topic_recommendations and study_plan.description:
                    study_plan.description = study_plan.description
            except Exception as e:
                print(f"AI Error during study plan creation: {e}")
            
            study_plan.save()
            messages.success(request, f'Study plan "{study_plan.title}" created successfully! 🎉')
            return redirect('home')  # Redirect to dashboard/home instead of list
    else:
        form = StudyPlanForm()
        
        # Generate general AI recommendations to help user plan
        try:
            ai_recommendations = LearningAIService.generate_study_recommendations(
                learning_style=user.learningstyle,
                goals=user.goals
            )
        except Exception as e:
            print(f"AI Error: {e}")
            ai_recommendations = None
    
    return render(request, 'studyplan/create_study_plan.html', {
        'form': form,
        'name': request.session.get("app_user_name", "User"),
        'user': user,
        'ai_recommendations': ai_recommendations
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

@require_login
def get_resources(request, plan_id):
    """Get AI-powered learning resources with real links for a study plan using smart database system"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
    
    # Use SMART resource system (checks database first, then generates new ones)
    resources = LearningAIService.get_smart_resources(
        topic=study_plan.title,
        learning_style=user.learningstyle,
        resource_type="all",
        limit=8  # Show more resources on dedicated page
    )
    
    return render(request, 'studyplan/resources.html', {
        'study_plan': study_plan,
        'resources': resources,
        'user': user,
        'name': request.session.get("app_user_name", "User")
    })

