from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.conf.urls.static import static
from authentication.models import User as AppUser
from studyplan.models import StudyPlan
from core.ai_service import LearningAIService

@never_cache
def home(request):
    # Redirect to landing if not logged in
    if not request.session.get("app_user_id"):
        return redirect("landing")
    
    # Get user and AI recommendations
    user_id = request.session.get("app_user_id")
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        # User doesn't exist, clear session and redirect to landing
        request.session.flush()
        return redirect("landing")
    
    # Get all study plans for this user
    study_plans = StudyPlan.objects.filter(user=user).order_by('-date_created')[:6]  # Show latest 6
    study_plan_count = StudyPlan.objects.filter(user=user).count()
    
    # Generate AI recommendations
    recommendations = None
    try:
        recommendations = LearningAIService.generate_study_recommendations(
            goals=user.goals
        )
        
        # Use SMART resource system (database + AI) for recommendations
        if recommendations and 'recommended_resources' in recommendations:
            # Get topic from user's goals for better matching
            topic_keywords = user.goals.lower().split()[:3]  # First 3 words
            topic = ' '.join(topic_keywords) if topic_keywords else 'learning'
            
            # Replace generic recommendations with smart database-backed resources
            smart_resources = LearningAIService.get_smart_resources(
                topic=topic,
                resource_type="all",
                limit=5
            )
            
            # Update recommendations with smart resources
            recommendations['recommended_resources'] = smart_resources
                
    except Exception as e:
        print(f"AI Error: {e}")
        recommendations = None
    
    # Show authenticated home page with AI recommendations and study plans
    return render(request, "authentication/home.html", {
        "name": request.session.get("app_user_name") or "User",
        "user": user,
        "recommendations": recommendations,
        "study_plans": study_plans,
        "study_plan_count": study_plan_count
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("authentication.urls")),
    path("home/", home, name="home"),
    path("study-plans/", include("studyplan.urls")),
    path("progress/", include("progress.urls")),
    path("quiz/", include("quiz.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
