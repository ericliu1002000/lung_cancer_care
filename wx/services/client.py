"""初始化 WeChatClient 对象。"""

import os

from wechatpy import WeChatClient

WX_APPID = os.getenv("WX_APPID")
WX_APPSECRET = os.getenv("WX_APPSECRET")

wechat_client = WeChatClient(WX_APPID, WX_APPSECRET)
