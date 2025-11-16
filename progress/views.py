from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Progress, ResourceProgress, StudySession, Achievement
from studyplan.models import StudyPlan, StudyPlanResource
from authentication.models import User


def check_authentication(request):
    """Check if user is authenticated"""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def progress_dashboard(request):
    """Main progress dashboard showing all user's study plans and progress"""
    user = check_authentication(request)
    if not user:
        messages.error(request, 'Please log in to view your progress.')
        return redirect('authentication:login')
    
    # Get all study plans with progress
    study_plans = StudyPlan.objects.filter(user=user).prefetch_related('plan_resources', 'progress')
    
    # Create progress records for plans that don't have one
    for plan in study_plans:
        if not hasattr(plan, 'progress'):
            Progress.objects.create(
                user=user,
                study_plan=plan,
                total_resources=plan.plan_resources.count()
            )
    
    # Refresh to get progress data
    study_plans = StudyPlan.objects.filter(user=user).prefetch_related('plan_resources', 'progress')
    
    # Calculate overall statistics
    total_plans = study_plans.count()
    completed_plans = study_plans.filter(status='completed').count()
    active_plans = study_plans.filter(status='active').count()
    
    total_hours = Progress.objects.filter(user=user).aggregate(
        total=Sum('total_hours_spent')
    )['total'] or 0
    
    total_resources_completed = Progress.objects.filter(user=user).aggregate(
        total=Sum('completed_resources')
    )['total'] or 0
    
    # Recent study sessions
    recent_sessions = StudySession.objects.filter(user=user).order_by('-started_at')[:5]
    
    # Recent achievements
    recent_achievements = Achievement.objects.filter(user=user).order_by('-earned_at')[:5]
    
    # Get user's points and rank
    user_points = user.total_points
    user_rank = user.current_rank if user.current_rank > 0 else \
                User.objects.filter(total_points__gt=user.total_points).count() + 1
    
    context = {
        'study_plans': study_plans,
        'total_plans': total_plans,
        'completed_plans': completed_plans,
        'active_plans': active_plans,
        'total_hours': round(float(total_hours), 2),
        'total_resources_completed': total_resources_completed,
        'recent_sessions': recent_sessions,
        'recent_achievements': recent_achievements,
        'user_points': user_points,
        'user_rank': user_rank,
    }
    
    return render(request, 'progress/dashboard.html', context)


def study_plan_progress(request, plan_id):
    """Detailed progress view for a specific study plan"""
    user = check_authentication(request)
    if not user:
        messages.error(request, 'Please log in to view progress.')
        return redirect('authentication:login')
    
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
    
    # Get or create progress record
    progress, created = Progress.objects.get_or_create(
        user=user,
        study_plan=study_plan,
        defaults={'total_resources': study_plan.plan_resources.count()}
    )
    
    if created:
        progress.update_progress()
    
    # Get all resources with their progress
    plan_resources = study_plan.plan_resources.all().select_related('resource')
    
    # Create ResourceProgress for resources that don't have one
    for plan_resource in plan_resources:
        ResourceProgress.objects.get_or_create(
            user=user,
            study_plan_resource=plan_resource
        )
    
    # Refresh to get progress data
    plan_resources = study_plan.plan_resources.all().select_related('resource').prefetch_related('progress')
    
    # Get study sessions for this plan
    study_sessions = StudySession.objects.filter(
        user=user,
        study_plan=study_plan
    ).order_by('-started_at')[:10]
    
    # Calculate time remaining
    days_remaining = None
    if study_plan.end_date:
        today = timezone.now().date()
        days_remaining = (study_plan.end_date - today).days
    
    context = {
        'study_plan': study_plan,
        'progress': progress,
        'plan_resources': plan_resources,
        'study_sessions': study_sessions,
        'days_remaining': days_remaining,
    }
    
    return render(request, 'progress/study_plan_detail.html', context)


@require_http_methods(["POST"])
def toggle_resource_completion(request, resource_progress_id):
    """Toggle completion status of a resource"""
    user = check_authentication(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        resource_progress = get_object_or_404(ResourceProgress, id=resource_progress_id, user=user)
        
        if resource_progress.is_completed:
            resource_progress.mark_incomplete()
            action = 'unmarked'
        else:
            resource_progress.mark_completed()
            action = 'marked'
            
            # Check for achievements
            check_and_award_achievements(user)
        
        return JsonResponse({
            'success': True,
            'action': action,
            'is_completed': resource_progress.is_completed,
            'completion_percentage': float(resource_progress.progress_percentage)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def update_resource_progress(request, resource_progress_id):
    """Update progress percentage and notes for a resource"""
    user = check_authentication(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        resource_progress = get_object_or_404(ResourceProgress, id=resource_progress_id, user=user)
        
        # Get data from request
        percentage = request.POST.get('percentage')
        notes = request.POST.get('notes')
        time_spent = request.POST.get('time_spent')
        
        if percentage is not None:
            resource_progress.progress_percentage = Decimal(percentage)
            if not resource_progress.started_at:
                resource_progress.started_at = timezone.now()
        
        if notes is not None:
            resource_progress.notes = notes
        
        if time_spent is not None:
            resource_progress.time_spent = Decimal(time_spent)
        
        resource_progress.save()
        
        # Update overall progress
        progress = Progress.objects.filter(
            user=user,
            study_plan=resource_progress.study_plan_resource.study_plan
        ).first()
        if progress:
            progress.update_progress()
        
        return JsonResponse({
            'success': True,
            'progress_percentage': float(resource_progress.progress_percentage),
            'time_spent': float(resource_progress.time_spent)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def start_study_session(request, plan_id):
    """Start a new study session"""
    user = check_authentication(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
        resource_id = request.POST.get('resource_id')
        
        session = StudySession.objects.create(
            user=user,
            study_plan=study_plan,
            resource_id=resource_id if resource_id else None
        )
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'started_at': session.started_at.isoformat()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def end_study_session(request, session_id):
    """End a study session"""
    user = check_authentication(request)
    if not user:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        session = get_object_or_404(StudySession, id=session_id, user=user)
        notes = request.POST.get('notes', '')
        
        if notes:
            session.notes = notes
        
        session.end_session()
        
        # Check for achievements
        check_and_award_achievements(user)
        
        return JsonResponse({
            'success': True,
            'duration': float(session.duration),
            'ended_at': session.ended_at.isoformat()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def achievements_view(request):
    """View all user achievements"""
    user = check_authentication(request)
    if not user:
        messages.error(request, 'Please log in to view achievements.')
        return redirect('authentication:login')
    
    achievements = Achievement.objects.filter(user=user).order_by('-earned_at')
    
    # Calculate potential achievements
    total_hours = Progress.objects.filter(user=user).aggregate(
        total=Sum('total_hours_spent')
    )['total'] or 0
    
    total_resources = Progress.objects.filter(user=user).aggregate(
        total=Sum('completed_resources')
    )['total'] or 0
    
    completed_plans = StudyPlan.objects.filter(user=user, status='completed').count()
    
    # Get user's points and rank
    user_points = user.total_points
    user_rank = user.current_rank if user.current_rank > 0 else \
                User.objects.filter(total_points__gt=user.total_points).count() + 1
    
    context = {
        'achievements': achievements,
        'total_hours': float(total_hours),
        'total_resources': total_resources,
        'completed_plans': completed_plans,
        'user_points': user_points,
        'user_rank': user_rank,
    }
    
    return render(request, 'progress/achievements.html', context)


def check_and_award_achievements(user):
    """Check and award new achievements to user"""
    # First plan
    if StudyPlan.objects.filter(user=user).count() >= 1:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='first_plan',
            defaults={
                'title': 'Getting Started',
                'description': 'Created your first study plan!'
            }
        )
    
    # First resource completion
    completed_resources = Progress.objects.filter(user=user).aggregate(
        total=Sum('completed_resources')
    )['total'] or 0
    
    if completed_resources >= 1:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='first_completion',
            defaults={
                'title': 'First Steps',
                'description': 'Completed your first resource!'
            }
        )
    
    # Resource milestones
    if completed_resources >= 10:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='resources_10',
            defaults={
                'title': 'Learning Enthusiast',
                'description': 'Completed 10 resources!'
            }
        )
    
    if completed_resources >= 50:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='resources_50',
            defaults={
                'title': 'Knowledge Seeker',
                'description': 'Completed 50 resources!'
            }
        )
    
    # Study hours milestones
    total_hours = Progress.objects.filter(user=user).aggregate(
        total=Sum('total_hours_spent')
    )['total'] or 0
    
    if total_hours >= 10:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='hours_10',
            defaults={
                'title': 'Dedicated Learner',
                'description': 'Studied for 10 hours!'
            }
        )
    
    if total_hours >= 50:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='hours_50',
            defaults={
                'title': 'Study Warrior',
                'description': 'Studied for 50 hours!'
            }
        )
    
    if total_hours >= 100:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='hours_100',
            defaults={
                'title': 'Master Student',
                'description': 'Studied for 100 hours!'
            }
        )
    
    # Plan completion
    if StudyPlan.objects.filter(user=user, status='completed').count() >= 1:
        Achievement.objects.get_or_create(
            user=user,
            achievement_type='plan_completed',
            defaults={
                'title': 'Goal Achiever',
                'description': 'Completed your first study plan!'
            }
        )
