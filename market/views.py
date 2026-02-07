import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from wx.services.pay import verify_notify

from market.service.order import (
    OrderBusinessError,
    OrderCreateResult,
    PaymentNotifyError,
    ProductNotAvailableError,
    create_order_for_user,
    get_product_for_buy,
    handle_wechat_pay_success,
    render_service_content_markdown,
)

logger = logging.getLogger(__name__)


def product_buy_page(request: HttpRequest) -> HttpResponse:
    """
    服务包购买页：展示商品信息、Markdown 格式的服务内容以及相关协议链接。
    """

    product_id = request.GET.get("product_id")

    try:
        product = get_product_for_buy(product_id)
    except ProductNotAvailableError:
        raise Http404("当前没有可购买的服务包")
    except Exception as exc:
        logger.exception("获取商品失败: %s", exc)
        raise Http404("商品不存在或已下架")

    service_html = render_service_content_markdown(product.service_content)

    base_url = getattr(settings, "WEB_BASE_URL", "").rstrip("/")
    def _full_url(path: str) -> str:
        if not base_url:
            return path
        return f"{base_url}{path}"

    urls = {
        "member_agreement": _full_url("/p/docs/Member_Agreement/"),
        "privacy_policy": _full_url("/p/docs/Privacy_Policy/"),
        "user_policy": _full_url("/p/docs/User_Policy/"),
        "consent": _full_url("/p/docs/Consent/"),
    }

    return render(
        request,
        "market/product_buy.html",
        {
            "product": product,
            "service_html": mark_safe(service_html),
            "urls": urls,
        },
    )


@login_required
@require_POST
def create_order_api(request: HttpRequest) -> JsonResponse:
    """
    创建待支付订单并返回微信 JSAPI 支付参数。
    前端需先引导用户阅读并勾选协议，再调用该接口。
    """

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"code": 400, "message": "请求体格式错误"}, status=400)

    product_id = payload.get("product_id")
    if not product_id:
        return JsonResponse({"code": 400, "message": "缺少商品 ID"}, status=400)

    client_ip = request.META.get("REMOTE_ADDR") or "127.0.0.1"

    try:
        result: OrderCreateResult = create_order_for_user(
            user=request.user,
            product_id=product_id,
            client_ip=client_ip,
        )
    except OrderBusinessError as exc:
        return JsonResponse({"code": 400, "message": str(exc)}, status=400)
    except Exception as exc:  # pragma: no cover - network/IO
        logger.exception("创建订单失败: %s", exc)
        return JsonResponse({"code": 500, "message": "创建订单失败，请稍后重试"}, status=500)

    return JsonResponse(
        {
            "code": 200,
            "data": {
                "order_no": result.order.order_no,
                "pay_params": result.pay_params,
            },
        }
    )


def _build_wechat_xml(return_code: str, return_msg: str) -> str:
    return (
        "<xml>"
        f"<return_code><![CDATA[{return_code}]]></return_code>"
        f"<return_msg><![CDATA[{return_msg}]]></return_msg>"
        "</xml>"
    )


@csrf_exempt
def wechat_pay_notify(request: HttpRequest) -> HttpResponse:
    """
    微信支付结果异步通知回调。
    验签成功且支付成功时，将订单状态从 PENDING 更新为 PAID。
    """

    if request.method != "POST":
        return HttpResponse(_build_wechat_xml("FAIL", "Invalid method"), content_type="text/xml")

    try:
        data = verify_notify(request)
    except Exception as exc:  # pragma: no cover - 网络或签名错误
        logger.error("支付回调验签失败: %s", exc)
        return HttpResponse(
            _build_wechat_xml("FAIL", "签名失败"),
            content_type="text/xml",
        )

    try:
        handle_wechat_pay_success(data)
    except PaymentNotifyError as exc:
        logger.warning("支付回调业务失败: %s", exc)
        return HttpResponse(
            _build_wechat_xml("FAIL", str(exc)),
            content_type="text/xml",
        )
    except Exception as exc:  # pragma: no cover - 数据库异常
        logger.exception("处理支付回调异常: %s", exc)
        return HttpResponse(
            _build_wechat_xml("FAIL", "内部错误"),
            content_type="text/xml",
        )

    return HttpResponse(
        _build_wechat_xml("SUCCESS", "OK"),
        content_type="text/xml",
    )
