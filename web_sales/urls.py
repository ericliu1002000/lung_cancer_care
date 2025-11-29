from django.urls import path

from .views import (
    sales_dashboard,
    sales_change_password,
    
    patient_detail,
    
    update_patient_doctor,
    doctor_detail,
)

app_name = "web_sales"

urlpatterns = [
    path("sales/dashboard/", sales_dashboard, name="sales_dashboard"),
    path(
        "sales/password/change/",
        sales_change_password,
        name="sales_change_password",
    ),
    
    path(
        "sales/patient/<int:pk>/detail/",
        patient_detail,
        name="patient_detail",
    ),
    
    path(
        "sales/patient/<int:pk>/doctor/",
        update_patient_doctor,
        name="update_patient_doctor",
    ),
    path(
        "sales/doctor/<int:pk>/detail/",
        doctor_detail,
        name="doctor_detail",
    ),
]
