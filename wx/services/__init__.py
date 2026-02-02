"""Wechat service package."""

from .client import wechat_client
from .crypto import get_crypto
from .handlers import handle_message
from .oauth import get_oauth_url, get_user_info
from .templates import send_template_message
from .reply_text_template import TextTemplateService
from .task_notifications import (
    send_daily_task_creation_messages,
    send_daily_task_reminder_messages,
)
from .chat_notifications import send_chat_unread_notifications

__all__ = [
    "wechat_client",
    "get_crypto",
    "handle_message",
    "get_oauth_url",
    "get_user_info",
    "send_template_message",
    "send_daily_task_creation_messages",
    "send_daily_task_reminder_messages",
    "send_chat_unread_notifications",
]
