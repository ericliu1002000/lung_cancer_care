"""
【业务说明】users 应用 Service 层，封装登录等跨视图复用逻辑。
【用法】视图调用 AuthService 的方法以获得登录结果，避免重复代码。
"""

from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth import authenticate, get_backends, login

from users.models import CustomUser
from users import choices


class AuthService:
    """
    【业务说明】统一处理多端登录（微信、PC），保证 Session 统一维护。
    【返回值约定】所有登录方法返回 (success: bool, payload: CustomUser|str)。
    """

    def __init__(self) -> None:
        backends = getattr(settings, "AUTHENTICATION_BACKENDS", None) or [
            "django.contrib.auth.backends.ModelBackend"
        ]
        self.default_backend = backends[0]

    def _fetch_wechat_openid(self, code: str) -> str:
        """
        【业务说明】模拟用微信 code 换取 openid，生产环境需调用官方 API。
        【TODO】待对接公众号接口后替换真实实现。
        """

        return f"mock_{code}"

    def wechat_login(self, request, code: str) -> Tuple[bool, Optional[CustomUser]]:
        if not code:
            return False, "缺少 code 参数"

        openid = self._fetch_wechat_openid(code)
        user = CustomUser.objects.filter(wx_openid=openid).first()
        if not user:
            user = CustomUser.objects.create(
                wx_openid=openid,
                wx_nickname="微信用户",
                user_type=choices.UserType.PATIENT,
                is_active=True,
            )
        login(request, user, backend=self.default_backend)
        return True, user

    def pc_login(self, request, username: str, password: str) -> Tuple[bool, Optional[CustomUser]]:
        if not username or not password:
            return False, "请输入用户名和密码"
        user = authenticate(request, username=username, password=password)
        if not user:
            return False, "用户名或密码错误"
        login(request, user)
        return True, user
