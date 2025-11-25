"""模板消息发送逻辑。"""

from .client import wechat_client


def send_template_message(openid, template_id, data, url=None, mini_program=None):
    """发送模板消息。url 建议指向 OAuth 回调以便识别用户。"""

    # 注：业务上建议构造形如 /wx/auth/redirect?target=REAL_URL 的跳转链接，
    # 以便后端在 OAuth 回调中静默获取 OpenID 并绑定用户身份。
    return wechat_client.message.send_template(openid, template_id, data, url=url, miniprogram=mini_program)
