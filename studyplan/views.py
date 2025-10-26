from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
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
    """Delete a study plan and all related records"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
    
    if request.method == 'POST':
        title = study_plan.title
        
        # Delete the study plan (StudyPlanResource will auto-delete via CASCADE)
        try:
            study_plan.delete()
            messages.success(request, f'Study plan "{title}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting study plan: {str(e)}')
            print(f"Error during deletion: {e}")
        
        return redirect('list_study_plans')
    
    return render(request, 'studyplan/delete_confirm.html', {
        'study_plan': study_plan,
        'name': request.session.get("app_user_name", "User")
    })

@require_login
def get_resources(request, plan_id):
    """Get AI-powered learning resources with real links for a study plan using smart database system"""
    from django.db import connection
    from resources.models import Resource
    from studyplan.models import StudyPlanResource
    
    user_id = request.session.get("app_user_id")
    
    try:
        # Close old connections to prevent stale connection issues
        connection.close()
        
        user = User.objects.get(id=user_id)
        study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
        
        # Check if resources are already saved for this study plan
        existing_plan_resources = StudyPlanResource.objects.filter(study_plan=study_plan).select_related('resource')
        
        if existing_plan_resources.exists():
            # Use saved resources
            resources = [
                {
                    "title": spr.resource.title,
                    "type": spr.resource.resource_type,
                    "url": spr.resource.url,
                    "description": spr.resource.description,
                    "platform": spr.resource.platform,
                    "difficulty": spr.resource.difficulty,
                    "estimated_time": spr.resource.estimated_time,
                    "is_free": spr.resource.is_free
                }
                for spr in existing_plan_resources
            ]
        else:
            # Generate new resources via AI
            # Build rich context from study plan details
            duration_days = (study_plan.end_date - study_plan.start_date).days
            duration_weeks = duration_days // 7
            
            context = {
                'learning_style': user.learningstyle,
                'description': study_plan.description or 'No description provided',
                'learning_objective': study_plan.learning_objective,
                'preferred_resources': study_plan.preferred_resources or 'Any type',
                'duration': f"{duration_weeks} weeks ({duration_days} days)",
                'hours_per_week': f"{study_plan.estimated_hours_per_week} hours",
                'start_date': study_plan.start_date.strftime('%B %d, %Y'),
                'end_date': study_plan.end_date.strftime('%B %d, %Y'),
                'status': study_plan.status
            }
            
            # Use SMART resource system with FULL CONTEXT
            resources = LearningAIService.get_smart_resources(
                topic=study_plan.title,
                learning_style=user.learningstyle,
                resource_type="all",
                limit=8,
                context=context
            )
            
            # Save resources to database for this study plan
            for index, resource_data in enumerate(resources):
                try:
                    # Get or create the resource
                    resource, created = Resource.objects.get_or_create(
                        url=resource_data['url'],
                        defaults={
                            'topic': study_plan.title,
                            'title': resource_data['title'],
                            'description': resource_data.get('description', ''),
                            'resource_type': resource_data.get('type', 'article'),
                            'category': Resource.detect_category_from_topic(study_plan.title),
                            'difficulty': resource_data.get('difficulty', 'all'),
                            'platform': resource_data.get('platform', 'Web'),
                            'learning_style': user.learningstyle,
                            'estimated_time': resource_data.get('estimated_time', 'Varies'),
                            'is_free': resource_data.get('is_free', True),
                        }
                    )
                    
                    # Link resource to study plan
                    StudyPlanResource.objects.get_or_create(
                        study_plan=study_plan,
                        resource=resource,
                        defaults={'order_index': index}
                    )
                except Exception as e:
                    print(f"Error saving resource: {e}")
                    continue
        
        return render(request, 'studyplan/resources.html', {
            'study_plan': study_plan,
            'resources': resources,
            'user': user,
            'name': request.session.get("app_user_name", "User")
        })
    except Exception as e:
        # If database connection fails, try to reconnect
        connection.close()
        messages.error(request, "Database connection error. Please try again.")
        print(f"Database error in get_resources: {e}")
        return redirect('list_study_plans')

