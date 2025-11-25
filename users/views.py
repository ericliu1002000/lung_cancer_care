"""
【业务说明】users 应用视图层，承载登录等接口。
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
