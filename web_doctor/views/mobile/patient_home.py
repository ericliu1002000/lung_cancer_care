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

