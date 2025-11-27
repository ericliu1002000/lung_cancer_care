from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from users import choices
from users.services import AuthService, PatientService

auth_service = AuthService()
patient_service = PatientService()


def _ensure_wechat_user(request: HttpRequest) -> bool:
    """确保当前请求绑定了微信用户。"""

    if request.user.is_authenticated:
        return True
    code = request.GET.get("code")
    success, result = auth_service.wechat_login(request, code)
    if not success:
        messages.error(request, result or "微信身份校验失败，请重新扫码。")
        return False
    return True


def bind_landing(request: HttpRequest, patient_id: int) -> HttpResponse:
    """展示绑定落地页。"""

    try:
        patient = patient_service.get_profile_for_bind(patient_id)
    except ValidationError:
        raise Http404("患者档案不存在")

    family_relation_choices = [
        (value, label)
        for value, label in choices.RelationType.choices
        if value != choices.RelationType.SELF
    ]
    family_default = (
        family_relation_choices[0][0]
        if family_relation_choices
        else choices.RelationType.SPOUSE
    )

    logged_in = _ensure_wechat_user(request)
    if not logged_in:
        return render(
            request,
            "web_patient/bind_landing.html",
            {
                "patient": patient,
                "relation_self": choices.RelationType.SELF,
                "family_relation_choices": family_relation_choices,
                "family_default": family_default,
            },
        )

    if request.user.is_authenticated:
        already_bound = (
            patient.user_id == request.user.id
            or patient.relations.filter(user=request.user).exists()
        )
        if already_bound:
            return render(
                request,
                "web_patient/bind_success.html",
                {"patient": patient},
            )

    return render(
        request,
        "web_patient/bind_landing.html",
        {
            "patient": patient,
            "relation_self": choices.RelationType.SELF,
            "family_relation_choices": family_relation_choices,
            "family_default": family_default,
        },
    )


@require_POST
def bind_submit(request: HttpRequest, patient_id: int) -> HttpResponse:
    """提交绑定申请。"""

    if not request.user.is_authenticated:
        messages.error(request, "请先通过微信确认身份后再绑定。")
        return redirect(reverse("web_patient:bind_landing", args=[patient_id]))

    try:
        patient_service.get_profile_for_bind(patient_id)
    except ValidationError:
        raise Http404("患者档案不存在")

    try:
        relation_type = int(request.POST.get("relation_type", choices.RelationType.SELF))
    except (TypeError, ValueError):
        relation_type = choices.RelationType.SELF

    relation_name = (request.POST.get("relation_name") or "").strip()
    receive_notification = request.POST.get("receive_notification") == "on"

    try:
        patient = patient_service.process_binding(
            request.user,
            patient_id,
            relation_type,
            relation_name=relation_name,
            receive_alert_msg=receive_notification,
        )
    except ValidationError as exc:
        messages.error(request, exc.message)
        return redirect(reverse("web_patient:bind_landing", args=[patient_id]))

    return render(
        request,
        "web_patient/bind_success.html",
        {
            "patient": patient,
        },
    )
