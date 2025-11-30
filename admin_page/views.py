from django.shortcuts import render, redirect
from authentication.models import User as AppUser
from studyplan.models import StudyPlan

def home(request):
    user_id = request.session.get("app_user_id")
    if not user_id:
        return redirect("landing")

    try:
        user = AppUser.objects.get(id=user_id)
    except AppUser.DoesNotExist:
        request.session.flush()
        return redirect("landing")

    # Admin check (still only your logic)
    is_admin = (
        getattr(user, "is_admin", False)
        or getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
    )
    if hasattr(user, "role"):
        is_admin = (str(user.role).lower() == "admin")

    if not is_admin:
        return redirect("home")

    # Safe active count (uses status field from StudyPlan)
    try:
        active_count = StudyPlan.objects.filter(status__iexact="ACTIVE").count()
    except Exception:
        active_count = 0

    context = {
        "admin_user": user,
        "user_count": AppUser.objects.count(),
        "plan_count": StudyPlan.objects.count(),
        "active_count": active_count,
        "recent_users": AppUser.objects.order_by("-id")[:5],
        "recent_plans": StudyPlan.objects.select_related("user").order_by("-date_created")[:6],
    }
    return render(request, "admin/home.html", context)


# ✅ ADD THIS VIEW so admin_page/urls.py won't error
def plans_redirect(request):
    return redirect("/study-plans/")

