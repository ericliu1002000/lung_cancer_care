"""销售端患者录入视图。"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_date

from users import choices
from users.decorators import check_sales
from users.services.patient import PatientService
from regions.models import Province


@login_required
@check_sales
def patient_entry(request: HttpRequest) -> HttpResponse:
    """销售端患者档案录入。"""

    if request.method == "POST":
        birth_date = parse_date(request.POST.get("birth_date", ""))
        try:
            gender_value = int(request.POST.get("gender", choices.Gender.MALE))
        except (TypeError, ValueError):
            gender_value = choices.Gender.MALE

        data = {
            "name": request.POST.get("name", "").strip(),
            "gender": gender_value,
            "birth_date": birth_date,
            "phone": request.POST.get("phone", "").strip(),
            "address_detail": request.POST.get("address_detail", "").strip(),
            "province_id": request.POST.get("address_province"),
            "city_id": request.POST.get("address_city"),
            "ec_name": request.POST.get("ec_name", "").strip(),
            "ec_relation": request.POST.get("ec_relation", "").strip(),
            "ec_phone": request.POST.get("ec_phone", "").strip(),
            "diagnosis": request.POST.get("diagnosis", "").strip(),
            "pathology": request.POST.get("pathology", "").strip(),
            "tnm_stage": request.POST.get("tnm_stage", "").strip(),
            "gene_mutation": request.POST.get("gene_mutation", "").strip(),
            "surgery_info": request.POST.get("surgery_info", "").strip(),
            "doctor_note": request.POST.get("doctor_note", "").strip(),
            "risk_factors": request.POST.getlist("risk_factors"),
        }

        try:
            PatientService().create_full_patient_record(request.user, data)
        except ValidationError as exc:
            messages.error(request, exc.message)
        else:
            messages.success(request, "患者档案录入成功")
            return redirect("web_sales:sales_dashboard")

    risk_options = ["家族遗传", "吸烟", "职业暴露", "空气污染", "肺部慢病", "其它"]
    provinces = Province.objects.all().order_by("name")

    return render(
        request,
        "web_sales/patient_entry.html",
        {
            "gender_choices": choices.Gender.choices,
            "risk_options": risk_options,
            "provinces": provinces,
        },
    )
