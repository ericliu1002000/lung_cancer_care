from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from users.models import CustomUser
from wx.services.handlers import handle_message


class WechatScanHandlerTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            wx_openid="openid_family_scan",
            is_subscribe=True,
        )

    def _build_message(self, **kwargs):
        payload = {
            "type": "event",
            "event": "scan",
            "source": self.user.wx_openid,
            "key": None,
            "event_key": None,
            "scene_id": None,
        }
        payload.update(kwargs)
        return SimpleNamespace(**payload)

    @patch("wx.services.handlers.generate_menu_auth_url")
    @patch("wx.services.handlers.TextTemplateService.get_render_content")
    @patch("wx.services.handlers.auth_service.get_or_create_wechat_user")
    @patch("wx.services.handlers.wechat_client.user.get")
    def test_subscribe_family_qrcode_returns_family_bind_link(
        self,
        mock_wechat_get,
        mock_get_or_create,
        mock_render,
        mock_generate_menu_auth_url,
    ):
        mock_wechat_get.return_value = {"nickname": "Family"}
        mock_get_or_create.return_value = (self.user, False)
        mock_generate_menu_auth_url.return_value = "https://example.com/p/bind/12/"
        mock_render.side_effect = (
            lambda code, context=None: (
                "welcome"
                if code == "subscribe_welcome"
                else f"scan:{context['url']}"
            )
        )

        reply = handle_message(
            self._build_message(
                event="subscribe",
                event_key="qrscene_bind_family_12",
            )
        )

        self.assertIn("welcome", reply.content)
        self.assertIn("https://example.com/p/bind/12/", reply.content)
        mock_generate_menu_auth_url.assert_called_with(
            "web_patient:bind_landing",
            patient_id=12,
        )

    @patch("wx.services.handlers.generate_menu_auth_url")
    @patch("wx.services.handlers.TextTemplateService.get_render_content")
    @patch("wx.services.handlers.auth_service.get_or_create_wechat_user")
    def test_scan_family_qrcode_returns_family_bind_link(
        self,
        mock_get_or_create,
        mock_render,
        mock_generate_menu_auth_url,
    ):
        mock_get_or_create.return_value = (self.user, False)
        mock_generate_menu_auth_url.return_value = "https://example.com/p/bind/18/"
        mock_render.side_effect = (
            lambda code, context=None: f"{code}:{context['url']}"
        )

        reply = handle_message(
            self._build_message(
                event="scan",
                key="bind_family_18",
            )
        )

        self.assertIn("https://example.com/p/bind/18/", reply.content)
        mock_generate_menu_auth_url.assert_called_with(
            "web_patient:bind_landing",
            patient_id=18,
        )

    @patch("wx.services.handlers.generate_menu_auth_url")
    @patch("wx.services.handlers.TextTemplateService.get_render_content")
    @patch("wx.services.handlers.auth_service.get_or_create_wechat_user")
    def test_scan_patient_qrcode_remains_compatible(
        self,
        mock_get_or_create,
        mock_render,
        mock_generate_menu_auth_url,
    ):
        mock_get_or_create.return_value = (self.user, False)
        mock_generate_menu_auth_url.return_value = "https://example.com/p/bind/21/"
        mock_render.side_effect = (
            lambda code, context=None: f"{code}:{context['url']}"
        )

        reply = handle_message(
            self._build_message(
                event="scan",
                key="bind_patient_21",
            )
        )

        self.assertIn("https://example.com/p/bind/21/", reply.content)
        mock_generate_menu_auth_url.assert_called_with(
            "web_patient:bind_landing",
            patient_id=21,
        )
