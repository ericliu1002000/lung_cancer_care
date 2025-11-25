"""
【业务说明】部署时初始化超级管理员账号，读取环境变量创建或跳过。
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from users import choices


class Command(BaseCommand):
    help = "Initialize default superuser from environment variables."

    def handle(self, *args, **options):
        username = os.getenv("SUPER_USER_NAME")
        password = os.getenv("SUPER_USER_PASSWORD")
        phone = os.getenv("SUPER_USER_PHONE")
        email = os.getenv("SUPER_USER_EMAIL", "admin@example.com")

        missing = [
            key
            for key, value in {
                "SUPER_USER_NAME": username,
                "SUPER_USER_PASSWORD": password,
                "SUPER_USER_PHONE": phone,
            }.items()
            if not value
        ]
        if missing:
            raise CommandError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        User = get_user_model()
        exists = User.objects.filter(username=username).exists() or User.objects.filter(phone=phone).exists()
        if exists:
            self.stdout.write(self.style.SUCCESS("Superuser already exists. Skipping."))
            return

        User.objects.create_superuser(
            username=username,
            password=password,
            phone=phone,
            user_type=choices.UserType.ADMIN,
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )

        self.stdout.write(self.style.SUCCESS("Superuser created successfully."))
