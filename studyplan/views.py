from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from .models import StudyPlan
from .forms import StudyPlanForm
from authentication.models import User
from core.ai_quiz_service import QuizGenerationService
from core.ai_resource_service import ResourceGenerationService
from quiz.models import Quiz, Question, QuestionOption

def require_login(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get("app_user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper

def _is_admin(user):
    is_admin = (
        getattr(user, "is_admin", False)
        or getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
    )
    if hasattr(user, "role"):
        is_admin = (str(user.role).lower() == "admin")
    return is_admin

def _get_plan_for_user_or_admin(user, plan_id):
    if _is_admin(user):
        return get_object_or_404(StudyPlan, id=plan_id)
    return get_object_or_404(StudyPlan, id=plan_id, user=user)

@require_login
def list_study_plans(request):
    from progress.models import Progress, ResourceProgress
    from studyplan.models import StudyPlanResource
    
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)

    if _is_admin(user):
        study_plans = StudyPlan.objects.all().prefetch_related('plan_resources')
    else:
        study_plans = StudyPlan.objects.filter(user=user).prefetch_related('plan_resources')
    
    plans_with_progress = []
    for plan in study_plans:
        progress, created = Progress.objects.get_or_create(
            user=plan.user if _is_admin(user) else user,
            study_plan=plan,
            defaults={'total_resources': 0, 'completed_resources': 0}
        )
        if created or progress.total_resources == 0:
            progress.update_progress()
        plan.progress = progress
        plans_with_progress.append(plan)
    
    return render(request, 'studyplan/list_study_plans.html', {
        'study_plans': plans_with_progress,
        'name': request.session.get("app_user_name", "User")
    })

@require_login
def create_study_plan(request):
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        form = StudyPlanForm(request.POST)
        if form.is_valid():
            study_plan = form.save(commit=False)
            study_plan.user = user
            study_plan.save()
            
            try:
                quiz_data = QuizGenerationService.generate_quiz(
                    topic=study_plan.title,
                    difficulty="medium",
                    num_questions=3
                )
                
                quiz = Quiz.objects.create(
                    title=f"{study_plan.title} - AI Generated Quiz",
                    description=f"Automatically generated quiz for {study_plan.title}",
                    study_plan=study_plan,
                    total_questions=len(quiz_data.get("questions", [])),
                    status="published"
                )
                
                for idx, q_data in enumerate(quiz_data.get("questions", []), 1):
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data.get("question", ""),
                        order=idx
                    )
                    
                    correct_answer = q_data.get("answer", "a").lower()
                    for option_letter in ['a', 'b', 'c', 'd']:
                        QuestionOption.objects.create(
                            question=question,
                            option_text=q_data.get(option_letter, ""),
                            is_correct=(option_letter == correct_answer),
                            order=ord(option_letter) - ord('a')
                        )
                
                messages.success(request, f'Study plan created with AI-generated quiz! 🎉')
                
            except Exception:
                messages.success(request, f'Study plan "{study_plan.title}" created successfully! 🎉')
            
            return redirect('home')
    else:
        form = StudyPlanForm()
    
    return render(request, 'studyplan/create_study_plan.html', {
        'form': form,
        'name': request.session.get("app_user_name", "User"),
        'user': user
    })

@require_login
def edit_study_plan(request, plan_id):
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)

    study_plan = _get_plan_for_user_or_admin(user, plan_id)
    
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
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)

    study_plan = _get_plan_for_user_or_admin(user, plan_id)
    
    if request.method == 'POST':
        title = study_plan.title
        try:
            study_plan.delete()
            messages.success(request, f'Study plan "{title}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting study plan: {str(e)}')
        
        return redirect('list_study_plans')
    
    return render(request, 'studyplan/delete_confirm.html', {
        'study_plan': study_plan,
        'name': request.session.get("app_user_name", "User")
    })

@require_login
def get_resources(request, plan_id):
    from resources.models import Resource
    from studyplan.models import StudyPlanResource
    from progress.models import Progress, ResourceProgress
    
    user_id = request.session.get("app_user_id")
    
    try:
        connection.close()
        user = User.objects.get(id=user_id)

        study_plan = _get_plan_for_user_or_admin(user, plan_id)
        plan_owner = study_plan.user
        
        progress, created = Progress.objects.get_or_create(
            user=plan_owner,
            study_plan=study_plan,
            defaults={'total_resources': 0, 'completed_resources': 0}
        )
        
        existing_plan_resources = StudyPlanResource.objects.filter(
            study_plan=study_plan
        ).select_related('resource')
        
        if existing_plan_resources.exists():
            resources = []
            for spr in existing_plan_resources:
                resource_progress, _ = ResourceProgress.objects.get_or_create(
                    user=plan_owner,
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
            
            resources_data = ResourceGenerationService.generate_resources(
                topic=study_plan.title,
                resource_type="all",
                limit=5,
                context=context,
                topic_category=study_plan.topic_category
            )
            
            resources = []
            for index, resource_data in enumerate(resources_data):
                try:
                    resource, _ = Resource.objects.get_or_create(
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
                    
                    spr, _ = StudyPlanResource.objects.get_or_create(
                        study_plan=study_plan,
                        resource=resource,
                        defaults={
                            'order_index': index,
                            'priority': index
                        }
                    )
                    
                    resource_progress, _ = ResourceProgress.objects.get_or_create(
                        user=plan_owner,
                        study_plan_resource=spr,
                        defaults={'is_completed': False}
                    )
                    
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
                except Exception:
                    continue
            
            progress.update_progress()
        
        return render(request, 'studyplan/resources.html', {
            'study_plan': study_plan,
            'resources': resources,
            'progress': progress,
            'user': plan_owner,
            'name': request.session.get("app_user_name", "User")
        })
    except Exception:
        connection.close()
        messages.error(request, "Database connection error. Please try again.")
        return redirect('list_study_plans')

@require_login
def add_selected_resources(request, plan_id):
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
        study_plan = _get_plan_for_user_or_admin(user, plan_id)
        plan_owner = study_plan.user
        
        data = json.loads(request.body)
        selected_resources = data.get('resources', [])
        
        if not selected_resources:
            return JsonResponse({'success': False, 'error': 'No resources selected'}, status=400)
        
        max_order = StudyPlanResource.objects.filter(study_plan=study_plan).count()
        
        saved_count = 0
        for index, resource_data in enumerate(selected_resources):
            try:
                resource, _ = Resource.objects.get_or_create(
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
                
                spr, spr_created = StudyPlanResource.objects.get_or_create(
                    study_plan=study_plan,
                    resource=resource,
                    defaults={
                        'order_index': max_order + index,
                        'priority': max_order + index
                    }
                )
                
                if spr_created:
                    ResourceProgress.objects.get_or_create(
                        user=plan_owner,
                        study_plan_resource=spr,
                        defaults={'is_completed': False}
                    )
                    saved_count += 1
                    
            except Exception:
                continue
        
        progress = Progress.objects.get(user=plan_owner, study_plan=study_plan)
        progress.update_progress()
        
        return JsonResponse({
            'success': True,
            'saved_count': saved_count,
            'message': f'Successfully added {saved_count} resource{"s" if saved_count != 1 else ""} to your study plan!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_login
def toggle_resource_completion(request, plan_id, resource_id):
    from progress.models import Progress, ResourceProgress
    from studyplan.models import StudyPlanResource
    from django.http import JsonResponse
    
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    try:
        study_plan = _get_plan_for_user_or_admin(user, plan_id)
        plan_owner = study_plan.user

        study_plan_resource = get_object_or_404(
            StudyPlanResource, id=resource_id, study_plan=study_plan
        )
        
        resource_progress, _ = ResourceProgress.objects.get_or_create(
            user=plan_owner,
            study_plan_resource=study_plan_resource
        )
        
        if resource_progress.is_completed:
            resource_progress.mark_incomplete()
            status = 'incomplete'
        else:
            resource_progress.mark_completed()
            status = 'completed'
        
        progress = Progress.objects.get(user=plan_owner, study_plan=study_plan)
        
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        else:
            messages.error(request, "Error updating resource status.")
            return redirect('study_plan_resources', plan_id=plan_id)

@require_login
def study_plan_progress(request, plan_id):
    from progress.models import Progress, ResourceProgress
    from studyplan.models import StudyPlanResource
    from quiz.models import Quiz, QuizAttempt
    
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)

    study_plan = _get_plan_for_user_or_admin(user, plan_id)
    plan_owner = study_plan.user
    
    progress, created = Progress.objects.get_or_create(
        user=plan_owner,
        study_plan=study_plan,
        defaults={'total_resources': 0, 'completed_resources': 0}
    )
    
    if created or progress.total_resources == 0:
        progress.update_progress()
    
    quiz_count = Quiz.objects.filter(study_plan=study_plan).count()
    quiz_attempts_count = QuizAttempt.objects.filter(
        user=plan_owner,
        quiz__study_plan=study_plan
    ).count()
    
    user_rank = plan_owner.current_rank if plan_owner.current_rank > 0 else \
                User.objects.filter(total_points__gt=plan_owner.total_points).count() + 1
    
    return render(request, 'studyplan/progress_detail.html', {
        'study_plan': study_plan,
        'progress': progress,
        'user': plan_owner,
        'name': request.session.get("app_user_name", "User"),
        'quiz_count': quiz_count,
        'quiz_attempts_count': quiz_attempts_count,
        'user_rank': user_rank,
    })
