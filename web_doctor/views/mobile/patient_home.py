from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from users.decorators import check_doctor_or_assistant

from web_doctor.views.workspace import _get_workspace_patients


@login_required
@check_doctor_or_assistant
def mobile_patient_home(request: HttpRequest, patient_id: int) -> HttpResponse:
    patients_qs = _get_workspace_patients(request.user, query=None).select_related("user")
    patient = patients_qs.filter(pk=patient_id).first()
    if patient is None:
        raise Http404("未找到患者")

    context = {
        "patient": patient,
        "patient_no": f"P{patient.id:06d}",
    }
    return render(request, "web_doctor/mobile/patient_home.html", context)


@login_required
@check_doctor_or_assistant
def mobile_patient_section(request: HttpRequest, patient_id: int, section: str) -> HttpResponse:
    patients_qs = _get_workspace_patients(request.user, query=None).select_related("user")
    patient = patients_qs.filter(pk=patient_id).first()
    if patient is None:
        raise Http404("未找到患者")

    valid_sections = {
        "indicators": "管理指标",
        "records": "诊疗记录",
        "todo": "患者待办",
        "chat": "患者咨询",
    }
    if section not in valid_sections:
        raise Http404("未找到页面")

    context = {
        "patient": patient,
        "patient_no": f"P{patient.id:06d}",
        "section": section,
        "section_title": valid_sections[section],
    }
    return render(request, "web_doctor/mobile/patient_section_placeholder.html", context)

