from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.conf.urls.static import static
from authentication.models import User as AppUser
from studyplan.models import StudyPlan

@never_cache
def home(request):
    # Redirect to landing if not logged in
    if not request.session.get("app_user_id"):
        return redirect("landing")
    
    # Get user
    user_id = request.session.get("app_user_id")
    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        # User doesn't exist, clear session and redirect to landing
        request.session.flush()
        return redirect("landing")
    
    # Get all study plans for this user (single query)
    all_plans = StudyPlan.objects.filter(user=user).order_by('-date_created')
    study_plan_count = all_plans.count()
    study_plans = all_plans[:6]  # Show latest 6
    
    # Get user's rank
    user_rank = user.current_rank if user.current_rank > 0 else \
                AppUser.objects.filter(total_points__gt=user.total_points).count() + 1

    # ✅ ADD THIS: detect if user is admin
    is_admin = (
        getattr(user, "is_admin", False)
        or getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
    )
    if hasattr(user, "role"):
        is_admin = (str(user.role).lower() == "admin")
    
    # Show dashboard with user data + admin flag
    return render(request, "authentication/home.html", {
        "name": request.session.get("app_user_name") or "User",
        "user": user,
        "study_plans": study_plans,
        "study_plan_count": study_plan_count,
        "user_rank": user_rank,
        "is_admin": is_admin,   # ✅ PASS TO TEMPLATE
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("authentication.urls")),
    path("home/", home, name="home"),
    path("study-plans/", include("studyplan.urls")),
    path("progress/", include("progress.urls")),
    path("quiz/", include("quiz.urls")),

    path("panel/", include(("admin_page.urls", "admin_page"), namespace="admin_page")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
