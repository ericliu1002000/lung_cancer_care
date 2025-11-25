"""初始化 AES 加解密器。"""

import os

from wechatpy.crypto import WeChatCrypto

WX_TOKEN = os.getenv("WX_TOKEN")
WX_ENCODING_AES_KEY = os.getenv("WX_ENCODING_AES_KEY")
WX_APPID = os.getenv("WX_APPID")

_wechat_crypto = None

if all([WX_TOKEN, WX_ENCODING_AES_KEY, WX_APPID]):
    _wechat_crypto = WeChatCrypto(WX_TOKEN, WX_ENCODING_AES_KEY, WX_APPID)


def get_crypto():
    """惰性返回 WeChatCrypto，缺少配置时给出提示。"""

    if not _wechat_crypto:
        raise RuntimeError("请先在 .env 中配置 WX_TOKEN/WX_ENCODING_AES_KEY/WX_APPID")
    return _wechat_crypto
