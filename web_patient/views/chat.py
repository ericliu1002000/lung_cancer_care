from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from users.decorators import auto_wechat_login, check_patient

@auto_wechat_login
@check_patient
def consultation_chat(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】医患咨询聊天页面
    【模板】`web_patient/consultation_chat.html`
    """
    patient = request.patient
    patient_id = request.GET.get("patient_id") or (patient.id if patient else None)
    
    context = {
        "patient": patient,
        "patient_id": patient_id,
    }
    return render(request, "web_patient/consultation_chat.html", context)
