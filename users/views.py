"""
【业务说明】users 应用视图层占位，后续会承载登录、扫码认领等接口。
【用法】定义 Class-Based View 并调用 Service 层。
【使用示例】`class PatientClaimView(View): ...`。
【参数】模块级无。
【返回值】无。
"""

from django.http import HttpResponse


def placeholder_view(request):
    """
    【业务说明】示例函数，提示未来需改为类视图实现。
    【用法】开发阶段可用于快速验证模板。
    【参数】request: HttpRequest。
    【返回值】HttpResponse，当前渲染简单模板。
    【使用示例】`path('users/demo/', placeholder_view)`。
    """

    return HttpResponse("users placeholder view")
