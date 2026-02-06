from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from users.models import PatientProfile
from wx.services.task_notifications import (
    _build_template_data,
    _get_dashboard_url,
    _get_wechat_template_id,
    _send_wechat_template_message,
)


class Command(BaseCommand):
    help = "Send a WeChat daily-task template message to a patient."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--patient-id",
            type=int,
            required=True,
            help="Target patient profile ID.",
        )
        parser.add_argument(
            "--content",
            type=str,
            default="",
            help="Message content to use in the template.",
        )

    def handle(self, *args, **options) -> None:
        patient_id = options.get("patient_id")
        content = (options.get("content") or "").strip()

        patient = (
            PatientProfile.objects.select_related("user")
            .filter(pk=patient_id)
            .first()
        )
        if not patient:
            raise CommandError(f"Patient not found: {patient_id}")

        user = patient.user
        if not user or not user.is_active:
            raise CommandError("Target user is missing or inactive.")
        if not user.is_subscribe:
            raise CommandError("Target user has not subscribed to WeChat.")
        if not getattr(user, "is_receive_wechat_message", True):
            raise CommandError("Target user disabled WeChat messages.")
        if not user.wx_openid:
            raise CommandError("Target user has no wx_openid.")

        if not content:
            try:
                content = (input("请输入 content: ") or "").strip()
            except EOFError as exc:
                raise CommandError("Missing content.") from exc
        if not content:
            raise CommandError("Content cannot be empty.")

        template_id = _get_wechat_template_id()
        if not template_id:
            raise CommandError("Missing WECHAT_DAILY_TASK_TEMPLATE_ID.")
        dashboard_url = _get_dashboard_url()
        if not dashboard_url:
            raise CommandError("Missing dashboard URL.")

        send_time = timezone.localtime()
        data = _build_template_data(content=content, send_time=send_time)

        ok, error = _send_wechat_template_message(
            openid=user.wx_openid,
            template_id=template_id,
            data=data,
            url=dashboard_url,
        )
        if not ok:
            raise CommandError(f"Send failed: {error}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent template message to patient {patient_id}."
            )
        )
