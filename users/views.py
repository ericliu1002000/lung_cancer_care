"""
【业务说明】users 应用视图层，承载登录等接口。
"""

import io

import segno
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from users import choices
from users.models import DoctorStudio
from users.services import AuthService


auth_service = AuthService()


@csrf_exempt
def unified_login_view(request):
    """
    【业务说明】统一处理微信 code 登录（GET）与 PC 账号密码登录（POST）。
    【参数】request：Django HttpRequest。
    【返回值】JsonResponse，包含 success 与 message。
    """

    if request.method == "GET":
        code = request.GET.get("code")
        success, payload = auth_service.wechat_login(request, code)
        if success:
            return JsonResponse({"success": True, "user_id": payload.id})
        return JsonResponse({"success": False, "message": payload}, status=400)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        success, payload = auth_service.pc_login(request, username, password)
        if success:
            return JsonResponse({"success": True, "user_id": payload.id})
        return JsonResponse({"success": False, "message": payload}, status=400)

    return JsonResponse({"success": False, "message": "不支持的请求方法"}, status=405)


@login_required
@require_GET
def generate_studio_qrcode(request, studio_id):
    """返回医生工作室的二维码 PNG 流，使用 segno 高性能生成器。

    TODO: 待确定正式域名后，将 `base_url` 替换为真实地址。
    仅允许医生、销售、医生助理访问。
    """


    studio = get_object_or_404(DoctorStudio, pk=studio_id)
    base_url = "https://TODO-domain/join/"
    qr_url = f"{base_url}{studio.code}/"
    qr = segno.make(qr_url)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=6)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = f'inline; filename="studio_{studio.id}.png"'
    return response
