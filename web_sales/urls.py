from django.urls import path

from .views import sales_dashboard, sales_change_password

app_name = "web_sales"

urlpatterns = [
    path("sales/dashboard/", sales_dashboard, name="sales_dashboard"),
    path(
        "sales/password/change/",
        sales_change_password,
        name="sales_change_password",
    ),
]
