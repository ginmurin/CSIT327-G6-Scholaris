from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.conf import settings

from authentication.models import User as AppUser
from studyplan.models import StudyPlan
from quiz.models import Quiz


def _profile_src(u):
    pic = getattr(u, "profile_picture", None)
    if not pic:
        return None

    try:
        url = pic.url
        if url:
            return url
    except Exception:
        pass

    pic_str = str(pic).strip()
    if not pic_str:
        return None

    if pic_str.startswith("http://") or pic_str.startswith("https://"):
        return pic_str

    supa_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
    bucket = getattr(settings, "SUPABASE_BUCKET", "profile-pictures").strip().strip("/")

    if supa_url and bucket:
        if pic_str.startswith(bucket + "/"):
            pic_str = pic_str[len(bucket) + 1:]
        return f"{supa_url}/storage/v1/object/public/{bucket}/{pic_str}"

    return pic_str


def _is_admin(user):
    is_admin = (
        getattr(user, "is_admin", False)
        or getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
    )
    if hasattr(user, "role"):
        is_admin = (str(user.role).lower() == "admin")
    return is_admin


def home(request):
    user_id = request.session.get("app_user_id")
    if not user_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=user_id)
    if not _is_admin(admin_user):
        return redirect("home")

    try:
        active_count = StudyPlan.objects.filter(status__iexact="ACTIVE").count()
    except Exception:
        active_count = 0

    recent_users = list(AppUser.objects.order_by("-id")[:5])
    for u in recent_users:
        u.profile_src = _profile_src(u)

    admin_user.profile_src = _profile_src(admin_user)

    context = {
        "admin_user": admin_user,
        "user_count": AppUser.objects.count(),
        "plan_count": StudyPlan.objects.count(),
        "active_count": active_count,
        "recent_users": recent_users,
        "recent_plans": StudyPlan.objects.select_related("user").order_by("-date_created")[:6],
        "is_impersonating": bool(request.session.get("impersonate_original_admin_id")),
    }
    return render(request, "admin/home.html", context)


def users_list(request):
    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    q = request.GET.get("q", "").strip()
    users_qs = AppUser.objects.all().order_by("-id")
    if q:
        users_qs = users_qs.filter(Q(name__icontains=q) | Q(email__icontains=q))

    users = list(users_qs)
    for u in users:
        u.profile_src = _profile_src(u)

    admin_user.profile_src = _profile_src(admin_user)

    return render(request, "admin/users_list.html", {
        "admin_user": admin_user,
        "users": users,
        "q": q,
    })


def user_detail(request, user_id):
    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    target_user = get_object_or_404(AppUser, id=user_id)
    target_user.profile_src = _profile_src(target_user)

    plans = StudyPlan.objects.filter(user=target_user).order_by("-date_created")

    return render(request, "admin/user_detail.html", {
        "admin_user": admin_user,
        "target_user": target_user,
        "plans": plans,
    })


def open_plan(request, plan_id):
    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    plan = get_object_or_404(StudyPlan, id=plan_id)

    if not request.session.get("impersonate_original_admin_id"):
        request.session["impersonate_original_admin_id"] = admin_id

    request.session["app_user_id"] = plan.user.id
    request.session["app_user_name"] = getattr(plan.user, "name", getattr(plan.user, "username", "User"))

    return redirect("study_plan_progress", plan_id=plan.id)


def delete_user(request, user_id):
    if request.method != "POST":
        return redirect("admin_page:user_detail", user_id=user_id)

    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    target_user = get_object_or_404(AppUser, id=user_id)

    if target_user.id == admin_user.id:
        return redirect("admin_page:user_detail", user_id=user_id)

    target_user.delete()
    return redirect("admin_page:users_list")


def view_as_user(request, user_id):
    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    target_user = get_object_or_404(AppUser, id=user_id)

    request.session["impersonate_original_admin_id"] = admin_id
    request.session["app_user_id"] = target_user.id
    request.session["app_user_name"] = target_user.name

    return redirect("home")


def return_to_admin(request):
    original_admin_id = request.session.get("impersonate_original_admin_id")
    if not original_admin_id:
        return redirect("admin_page:home")

    admin_user = get_object_or_404(AppUser, id=original_admin_id)

    request.session["app_user_id"] = admin_user.id
    request.session["app_user_name"] = admin_user.name
    request.session.pop("impersonate_original_admin_id", None)

    return redirect("admin_page:home")


def quizzes_list(request):
    """Display all quizzes with their owners"""
    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    owner = request.GET.get("owner", "").strip()

    quizzes_qs = Quiz.objects.select_related("created_by").order_by("-created_at")

    if q:
        quizzes_qs = quizzes_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    if status:
        if status.lower() == 'published':
            # AI-generated quizzes should never be published (they're for user study plans only)
            quizzes_qs = quizzes_qs.filter(status__iexact=status, created_by__isnull=False)
        else:
            quizzes_qs = quizzes_qs.filter(status__iexact=status)
    
    if owner == "ai":
        quizzes_qs = quizzes_qs.filter(created_by__isnull=True)
    elif owner == "user":
        quizzes_qs = quizzes_qs.filter(created_by__isnull=False)

    quizzes = list(quizzes_qs)
    
    # Attach profile sources for all quiz creators
    for quiz in quizzes:
        if quiz.created_by:
            quiz.created_by.profile_src = _profile_src(quiz.created_by)

    admin_user.profile_src = _profile_src(admin_user)

    return render(request, "admin/quizzes_list.html", {
        "admin_user": admin_user,
        "quizzes": quizzes,
        "q": q,
        "status": status,
        "owner": owner,
    })


def delete_quiz(request, quiz_id):
    """Delete a quiz"""
    if request.method != "POST":
        return redirect("admin_page:quizzes_list")

    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Only allow deletion of user-created quizzes, not AI-generated ones
    if quiz.created_by:
        quiz.delete()

    return redirect("admin_page:quizzes_list")


def plans_list(request):
    """Display all study plans with their users"""
    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()

    plans_qs = StudyPlan.objects.select_related("user").order_by("-date_created")

    if q:
        plans_qs = plans_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    if status:
        plans_qs = plans_qs.filter(status__iexact=status)
    
    if category:
        plans_qs = plans_qs.filter(topic_category=category)

    plans = list(plans_qs)
    
    # Attach profile sources for all plan users
    for plan in plans:
        if plan.user:
            plan.user.profile_src = _profile_src(plan.user)

    admin_user.profile_src = _profile_src(admin_user)

    return render(request, "admin/plans_list.html", {
        "admin_user": admin_user,
        "plans": plans,
        "q": q,
        "status": status,
        "category": category,
        "topic_categories": StudyPlan.TOPIC_CATEGORIES,
    })


def delete_plan(request, plan_id):
    """Delete a study plan"""
    if request.method != "POST":
        return redirect("admin_page:plans_list")

    admin_id = request.session.get("app_user_id")
    if not admin_id:
        return redirect("landing")

    admin_user = get_object_or_404(AppUser, id=admin_id)
    if not _is_admin(admin_user):
        return redirect("home")

    plan = get_object_or_404(StudyPlan, id=plan_id)
    plan.delete()

    return redirect("admin_page:plans_list")
