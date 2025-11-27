from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from users.models import PatientRelation



def patient_dashboard(request: HttpRequest) -> HttpResponse:
    """患者端首页：根据本人或家属身份展示档案。"""

    patient = getattr(request.user, "patient_profile", None)
    is_family = False

    if patient is None:
        relation = (
            PatientRelation.objects.select_related("patient")
            .filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        if relation and relation.patient:
            patient = relation.patient
            is_family = True

    if patient is None:
        # TODO: 引导到 C 端自注册/资料填写页
        return redirect("web_patient:onboarding")

    return render(
        request,
        "web_patient/dashboard.html",
        {
            "patient": patient,
            "is_family": is_family,
        },
    )



def onboarding(request: HttpRequest) -> HttpResponse:
    """无档案用户的引导页。"""

    return render(request, "web_patient/onboarding.html")
