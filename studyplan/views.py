from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from .models import StudyPlan
from .forms import StudyPlanForm
from authentication.models import User
from core.ai_quiz_service import QuizGenerationService
from core.ai_resource_service import ResourceGenerationService
from quiz.models import Quiz, Question, QuestionOption

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
    """Display all study plans for the logged-in user with progress tracking"""
    from progress.models import Progress, ResourceProgress
    from studyplan.models import StudyPlanResource
    
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plans = StudyPlan.objects.filter(user=user).prefetch_related('plan_resources')
    
    # Add progress data to each study plan
    plans_with_progress = []
    for plan in study_plans:
        # Get or create progress record
        progress, created = Progress.objects.get_or_create(
            user=user,
            study_plan=plan,
            defaults={'total_resources': 0, 'completed_resources': 0}
        )
        
        # Update progress if needed
        if created or progress.total_resources == 0:
            progress.update_progress()
        
        # Add progress data to plan object
        plan.progress = progress
        plans_with_progress.append(plan)
    
    return render(request, 'studyplan/list_study_plans.html', {
        'study_plans': plans_with_progress,
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
            
            # Generate AI quizzes for the study plan
            try:
                print(f"\n🎯 Generating AI quiz for study plan: {study_plan.title}")
                quiz_data = QuizGenerationService.generate_quiz(
                    topic=study_plan.title,
                    difficulty="medium",
                    num_questions=3
                )
                
                # Create the quiz WITHOUT created_by so it appears in Available Quizzes
                quiz = Quiz.objects.create(
                    title=f"{study_plan.title} - AI Generated Quiz",
                    description=f"Automatically generated quiz for {study_plan.title}",
                    study_plan=study_plan,
                    total_questions=len(quiz_data.get("questions", [])),
                    status="published"
                )
                
                # Create questions from AI response
                for idx, q_data in enumerate(quiz_data.get("questions", []), 1):
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data.get("question", ""),
                        order=idx
                    )
                    
                    # Create options (a, b, c, d)
                    correct_answer = q_data.get("answer", "a").lower()
                    for option_letter in ['a', 'b', 'c', 'd']:
                        QuestionOption.objects.create(
                            question=question,
                            option_text=q_data.get(option_letter, ""),
                            is_correct=(option_letter == correct_answer),
                            order=ord(option_letter) - ord('a')
                        )
                
                print(f"✅ Created quiz with {len(quiz_data.get('questions', []))} questions!")
                messages.success(request, f'Study plan created with AI-generated quiz! 🎉')
                
            except Exception as e:
                print(f"❌ Error generating quiz: {e}")
                messages.success(request, f'Study plan "{study_plan.title}" created successfully! 🎉')
            
            return redirect('home')  # Redirect to dashboard/home instead of list
    else:
        form = StudyPlanForm()
    
    return render(request, 'studyplan/create_study_plan.html', {
        'form': form,
        'name': request.session.get("app_user_name", "User"),
        'user': user
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
    from progress.models import Progress, ResourceProgress
    
    user_id = request.session.get("app_user_id")
    
    try:
        # Close old connections to prevent stale connection issues
        connection.close()
        
        user = User.objects.get(id=user_id)
        study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
        
        # Get or create progress record
        progress, created = Progress.objects.get_or_create(
            user=user,
            study_plan=study_plan,
            defaults={'total_resources': 0, 'completed_resources': 0}
        )
        
        # Check if resources are already saved for this study plan
        existing_plan_resources = StudyPlanResource.objects.filter(study_plan=study_plan).select_related('resource')
        
        if existing_plan_resources.exists():
            # Use saved resources with progress tracking
            resources = []
            for spr in existing_plan_resources:
                # Get or create resource progress
                resource_progress, _ = ResourceProgress.objects.get_or_create(
                    user=user,
                    study_plan_resource=spr,
                    defaults={'is_completed': spr.is_completed}
                )
                
                resources.append({
                    "id": spr.id,
                    "title": spr.resource.title,
                    "type": spr.resource.resource_type,
                    "url": spr.resource.url,
                    "description": spr.resource.description,
                    "platform": spr.resource.platform,
                    "difficulty": spr.resource.difficulty,
                    "estimated_time": spr.resource.estimated_time,
                    "is_free": spr.resource.is_free,
                    "is_completed": spr.is_completed,
                    "progress_id": resource_progress.id
                })
        else:
            # Generate new resources via AI and save them automatically
            # Build rich context from study plan details
            duration_days = (study_plan.end_date - study_plan.start_date).days
            duration_weeks = duration_days // 7
            
            context = {
                'description': study_plan.description or 'No description provided',
                'learning_objective': study_plan.learning_objective,
                'preferred_resources': study_plan.preferred_resources or 'Any type',
                'duration': f"{duration_weeks} weeks ({duration_days} days)",
                'hours_per_week': f"{study_plan.estimated_hours_per_week} hours",
                'start_date': study_plan.start_date.strftime('%B %d, %Y'),
                'end_date': study_plan.end_date.strftime('%B %d, %Y'),
                'status': study_plan.status
            }
            
            # Use DeepSeek AI to generate resources with FULL CONTEXT
            resources_data = ResourceGenerationService.generate_resources(
                topic=study_plan.title,
                resource_type="all",
                limit=8,
                context=context,
                topic_category=study_plan.topic_category
            )
            
            print(f"Received {len(resources_data)} resources from AI service")
            
            # Save resources to database for this study plan
            resources = []  # Build list of saved resources
            for index, resource_data in enumerate(resources_data):
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
                            'estimated_time': resource_data.get('estimated_time', 'Varies'),
                            'is_free': resource_data.get('is_free', True),
                        }
                    )
                    
                    # Link resource to study plan
                    spr, _ = StudyPlanResource.objects.get_or_create(
                        study_plan=study_plan,
                        resource=resource,
                        defaults={
                            'order_index': index,
                            'priority': index  # Set priority to match order_index
                        }
                    )
                    
                    # Create resource progress
                    resource_progress, _ = ResourceProgress.objects.get_or_create(
                        user=user,
                        study_plan_resource=spr,
                        defaults={'is_completed': False}
                    )
                    
                    # Add to resources list for display
                    resources.append({
                        "id": spr.id,
                        "title": resource.title,
                        "type": resource.resource_type,
                        "url": resource.url,
                        "description": resource.description,
                        "platform": resource.platform,
                        "difficulty": resource.difficulty,
                        "estimated_time": resource.estimated_time,
                        "is_free": resource.is_free,
                        "is_completed": spr.is_completed,
                        "progress_id": resource_progress.id
                    })
                    print(f"Saved and added resource: {resource.title}")
                except Exception as e:
                    print(f"Error saving resource '{resource_data.get('title', 'Unknown')}': {e}")
                    continue
            
            print(f"Successfully saved {len(resources)} resources to display")
            
            # Update progress count
            progress.update_progress()
        
        return render(request, 'studyplan/resources.html', {
            'study_plan': study_plan,
            'resources': resources,
            'progress': progress,
            'user': user,
            'name': request.session.get("app_user_name", "User")
        })
    except Exception as e:
        # If database connection fails, try to reconnect
        connection.close()
        messages.error(request, "Database connection error. Please try again.")
        print(f"Database error in get_resources: {e}")
        return redirect('list_study_plans')

@require_login
def add_selected_resources(request, plan_id):
    """Save selected AI-suggested resources to the study plan"""
    from django.http import JsonResponse
    from resources.models import Resource
    from studyplan.models import StudyPlanResource
    from progress.models import Progress, ResourceProgress
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
    
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    try:
        study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
        
        # Parse the selected resources from request body
        data = json.loads(request.body)
        selected_resources = data.get('resources', [])
        
        if not selected_resources:
            return JsonResponse({'success': False, 'error': 'No resources selected'}, status=400)
        
        # Get current max order_index
        max_order = StudyPlanResource.objects.filter(study_plan=study_plan).count()
        
        saved_count = 0
        for index, resource_data in enumerate(selected_resources):
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
                        'estimated_time': resource_data.get('estimated_time', 'Varies'),
                        'is_free': resource_data.get('is_free', True),
                    }
                )
                
                # Link resource to study plan (check if not already linked)
                spr, spr_created = StudyPlanResource.objects.get_or_create(
                    study_plan=study_plan,
                    resource=resource,
                    defaults={
                        'order_index': max_order + index,
                        'priority': max_order + index
                    }
                )
                
                if spr_created:
                    # Create resource progress
                    ResourceProgress.objects.get_or_create(
                        user=user,
                        study_plan_resource=spr,
                        defaults={'is_completed': False}
                    )
                    saved_count += 1
                    print(f"Saved resource: {resource.title}")
                    
            except Exception as e:
                print(f"Error saving resource '{resource_data.get('title', 'Unknown')}': {e}")
                continue
        
        # Update progress
        progress = Progress.objects.get(user=user, study_plan=study_plan)
        progress.update_progress()
        
        return JsonResponse({
            'success': True,
            'saved_count': saved_count,
            'message': f'Successfully added {saved_count} resource{"s" if saved_count != 1 else ""} to your study plan!'
        })
        
    except Exception as e:
        print(f"Error in add_selected_resources: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_login
def toggle_resource_completion(request, plan_id, resource_id):
    """Toggle completion status of a resource"""
    from progress.models import Progress, ResourceProgress
    from studyplan.models import StudyPlanResource
    from django.http import JsonResponse
    
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    try:
        study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
        study_plan_resource = get_object_or_404(StudyPlanResource, id=resource_id, study_plan=study_plan)
        
        # Get or create resource progress
        resource_progress, _ = ResourceProgress.objects.get_or_create(
            user=user,
            study_plan_resource=study_plan_resource
        )
        
        # Toggle completion
        if resource_progress.is_completed:
            resource_progress.mark_incomplete()
            status = 'incomplete'
        else:
            resource_progress.mark_completed()
            status = 'completed'
        
        # Get updated progress
        progress = Progress.objects.get(user=user, study_plan=study_plan)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'status': status,
                'is_completed': resource_progress.is_completed,
                'completion_percentage': float(progress.completion_percentage),
                'completed_resources': progress.completed_resources,
                'total_resources': progress.total_resources
            })
        else:
            messages.success(request, f'Resource marked as {status}!')
            return redirect('study_plan_resources', plan_id=plan_id)
            
    except Exception as e:
        print(f"Error toggling completion: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        else:
            messages.error(request, "Error updating resource status.")
            return redirect('study_plan_resources', plan_id=plan_id)

@require_login
def study_plan_progress(request, plan_id):
    """Show progress page for a specific study plan"""
    from progress.models import Progress, ResourceProgress
    from studyplan.models import StudyPlanResource
    from quiz.models import Quiz, QuizAttempt
    
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
    
    # Get or create progress record
    progress, created = Progress.objects.get_or_create(
        user=user,
        study_plan=study_plan,
        defaults={'total_resources': 0, 'completed_resources': 0}
    )
    
    # Update progress if needed
    if created or progress.total_resources == 0:
        progress.update_progress()
    
    # Get quiz statistics
    quiz_count = Quiz.objects.filter(study_plan=study_plan).count()
    quiz_attempts_count = QuizAttempt.objects.filter(
        user=user,
        quiz__study_plan=study_plan
    ).count()
    
    # Get user's rank
    user_rank = user.current_rank if user.current_rank > 0 else \
                User.objects.filter(total_points__gt=user.total_points).count() + 1
    
    return render(request, 'studyplan/progress_detail.html', {
        'study_plan': study_plan,
        'progress': progress,
        'user': user,
        'name': request.session.get("app_user_name", "User"),
        'quiz_count': quiz_count,
        'quiz_attempts_count': quiz_attempts_count,
        'user_rank': user_rank,
    })

