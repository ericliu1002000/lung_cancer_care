from django.urls import path

from . import views

app_name = "market"

urlpatterns = [
    path("buy/", views.product_buy_page, name="product_buy"),
    path("api/create_order/", views.create_order_api, name="create_order_api"),
    path("api/pay/notify/", views.wechat_pay_notify, name="wechat_pay_notify"),
]

