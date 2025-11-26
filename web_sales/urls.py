from django.urls import path

from .views import sales_dashboard

app_name = "web_sales"

urlpatterns = [
    path("sales/dashboard/", sales_dashboard, name="sales_dashboard"),
]
