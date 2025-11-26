"""web_doctor 应用视图：登录、医生/销售工作台。"""

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from users.decorators import check_doctor_or_assistant
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from users import choices
from users.services.auth import AuthService

from .forms import DoctorPasswordChangeForm


def login_view(request: HttpRequest) -> HttpResponse:
    """登录入口，依据 user_type 跳转不同 Dashboard。"""
    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        success, payload = AuthService().pc_login(request, phone, password)
        if success:
            user = payload
            if user.user_type in {choices.UserType.DOCTOR, choices.UserType.ASSISTANT}:
                return redirect("web_doctor:doctor_dashboard")
            if user.user_type == choices.UserType.SALES:
                return redirect("web_sales:sales_dashboard")
            logout(request)
            messages.error(request, "当前账号无医生/销售权限")
        else:
            messages.error(request, payload)
    return render(request, "login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    """退出登录后回到登录页。"""

    logout(request)
    return redirect("web_doctor:login")


@login_required
@check_doctor_or_assistant
def doctor_dashboard(request: HttpRequest) -> HttpResponse:
    """医生端 Dashboard：展示医生信息与患者列表。"""

    doctor_profile = getattr(request.user, "doctor_profile", None)
    if doctor_profile is None:
        assistant_profile = getattr(request.user, "assistant_profile", None)
        if assistant_profile:
            doctor_profile = assistant_profile.doctors.select_related("user").first()
    if doctor_profile is None:
        raise Http404("当前账号未绑定医生档案")

    patients = doctor_profile.patients.filter(is_active=True).order_by("-created_at")

    context = {
        "doctor": doctor_profile,
        "patients": patients,
    }
    return render(request, "web_doctor/dashboard.html", context)


@login_required
@check_doctor_or_assistant
def doctor_change_password(request: HttpRequest) -> HttpResponse:
    """医生端修改密码。"""

    if request.method == "POST":
        form = DoctorPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "密码修改成功")
            return redirect("web_doctor:doctor_dashboard")
        messages.error(request, "请检查输入是否正确")
    else:
        form = DoctorPasswordChangeForm(request.user)

    return render(
        request,
        "web_doctor/change_password.html",
        {
            "form": form,
        },
    )

