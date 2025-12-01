# wx/services/pay.py
import logging
from django.conf import settings
from wechatpy.pay import WeChatPay
from wechatpy.exceptions import WeChatPayException

logger = logging.getLogger(__name__)

# 初始化支付客户端
# 修正说明：
# 1. api_key: 对应商户平台设置的 32 位 API v2 密钥 (settings.WX_MCH_KEY)
# 2. mch_key: 对应商户私钥证书文件的路径 (settings.WX_PAY_KEY_PATH)
wx_pay_client = WeChatPay(
    appid=settings.WX_APPID,
    api_key=settings.WX_MCH_KEY,         # <--- 修正这里：API密钥
    mch_id=settings.WX_MCH_ID,
    mch_cert=settings.WX_PAY_CERT_PATH,  # 公钥证书路径
    mch_key=settings.WX_PAY_KEY_PATH     # <--- 修正这里：私钥文件路径 (注意参数名是 mch_key)
)

def create_jsapi_params(openid, order_no, amount, body="岱劲健康-服务包", client_ip=None):
    """
    统一下单并获取前端 JSSDK 支付参数
    """
    try:
        # 微信金额单位是分，需要转换
        total_fee = int(amount * 100)
        # 避免测试时出现 0 元报错
        if total_fee <= 0: total_fee = 1

        # 1. 调用微信统一下单接口
        order_res = wx_pay_client.order.create(
            trade_type="JSAPI",
            body=body,
            total_fee=total_fee,
            notify_url=settings.WX_PAY_NOTIFY_URL,
            user_id=openid,
            out_trade_no=order_no,
            client_ip=client_ip or "127.0.0.1"
        )
        
        prepay_id = order_res.get("prepay_id")
        
        # 2. 生成前端 JS 需要的签名参数
        jsapi_params = wx_pay_client.jsapi.get_jsapi_params(prepay_id)
        
        return jsapi_params

    except WeChatPayException as e:
        logger.error(f"微信下单失败: {e.return_code} - {e.return_msg} - {e.err_code_des}")
        raise Exception(f"支付请求失败: {e.err_code_des or e.return_msg}")

def verify_notify(request):
    """验证并解析微信支付回调通知"""
    try:
        # wechatpy 会自动验证签名
        data = wx_pay_client.parse_payment_result(request.body)
        return data
    except Exception as e:
        logger.error(f"回调验签失败: {e}")
        raise