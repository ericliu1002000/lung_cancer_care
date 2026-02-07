"""Send daily task reminder messages for pending tasks."""

from __future__ import annotations

from datetime import date, datetime

from django.core.management.base import BaseCommand, CommandError

from wx.services import send_daily_task_reminder_messages


class Command(BaseCommand):
    help = "Send reminder messages for pending daily tasks (default: today)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--date",
            dest="task_date",
            help="Target date in YYYY-MM-DD format. Defaults to today.",
        )

    def handle(self, *args, **options) -> None:
        task_date = date.today()
        raw_date = options.get("task_date")
        if raw_date:
            try:
                task_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("Invalid --date, expected YYYY-MM-DD.") from exc

        sent_count = send_daily_task_reminder_messages(task_date)
        self.stdout.write(
            self.style.SUCCESS(
                f"Sent {sent_count} daily task reminder message(s)."
            )
        )
