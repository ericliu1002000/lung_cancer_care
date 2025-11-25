from django.urls import path

from wx import views

app_name = "wx"

urlpatterns = [
    path("", views.wechat_main, name="wechat_main"),
]
