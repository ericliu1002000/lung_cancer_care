from django.urls import path

from users.views import generate_studio_qrcode

app_name = "users"

urlpatterns = [
    path("qrcode/<int:studio_id>/", generate_studio_qrcode, name="studio_qrcode"),
]
