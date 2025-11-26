from django.urls import path

from . import views

app_name = "web_doctor"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path(
        "doctor/password/change/",
        views.doctor_change_password,
        name="doctor_change_password",
    ),
    path("sales/dashboard/", views.sales_dashboard, name="sales_dashboard"),
]
