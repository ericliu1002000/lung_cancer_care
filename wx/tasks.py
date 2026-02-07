from celery import shared_task

from wx.services.chat_notifications import send_chat_unread_notification_for_message


@shared_task(name="wx.send_chat_unread_notification")
def send_chat_unread_notification_task(message_id: int) -> bool:
    return send_chat_unread_notification_for_message(message_id)
