from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.conf import settings

from authentication.models import User as AppUser
from studyplan.models import StudyPlan


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
