"""OAuth 相关逻辑。"""

from urllib.parse import quote

from .client import wechat_client


def get_oauth_url(redirect_uri, scope="snsapi_base", state="STATE"):
    """构造授权 URL，state 默认可自定义。"""

    return wechat_client.oauth.authorize_url(redirect_uri=redirect_uri, scope=scope, state=state)


def get_user_info(code):
    """通过 code 换取 openid 等信息。"""

    data = wechat_client.oauth.fetch_access_token(code)
    return data
