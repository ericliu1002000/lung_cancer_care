import uuid

from django.contrib.auth.base_user import BaseUserManager

from users import choices


class CustomUserManager(BaseUserManager):
    """
    【业务说明】封装自定义用户的创建流程，统一处理用户名生成、密码设定与字段校验。
    【用法】通过 `CustomUser.objects.create_user` 或 `create_superuser` 调用。
    【使用示例】`CustomUser.objects.create_user(phone="13800138000", user_type=choices.UserType.SALES)`。
    【参数】继承自 BaseUserManager，无额外初始化参数。
    【返回值】创建完成的用户实例。
    """

    use_in_migrations = True

    def _generate_username(self) -> str:
        """
        【业务说明】当外部未显式提供 username 时，需要生成唯一标识。
        【用法】内部调用，无需外部依赖。
        【参数】self：管理器实例。
        【返回值】str，保证 20 位随机后缀。
        【使用示例】create_user 时自动调用。
        """

        return f"user_{uuid.uuid4().hex[:20]}"

    def _create_user(self, username, password, **extra_fields):
        """
        【业务说明】统一的底层建号逻辑，负责密码处理与持久化。
        【用法】外部不要直接调用，使用 `create_user` / `create_superuser`。
        【参数】username: str，可为空；password: str，可为空；extra_fields: 业务字段。
        【返回值】CustomUser 实例。
        【使用示例】内部由 create_user 引用。
        """

        if not username:
            username = self._generate_username()
        user = self.model(username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, username=None, password=None, **extra_fields):
        """
        【业务说明】创建普通账号，默认 user_type=患者 且无后台权限。
        【用法】Service 或 View 调用以完成注册流程。
        【参数】username,str|None；password,str|None；extra_fields，自定义字段（如 phone,user_type）。
        【返回值】CustomUser。
        【使用示例】`CustomUser.objects.create_user(password=None, wx_openid="xxx")`。
        """

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("user_type", choices.UserType.PATIENT)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username=None, password=None, **extra_fields):
        """
        【业务说明】创建平台管理员账号，强制开启后台权限。
        【用法】`python manage.py createsuperuser` 会调用。
        【参数】同 create_user，额外需传递 password。
        【返回值】CustomUser。
        【使用示例】命令行交互式创建超级管理员。
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", choices.UserType.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)
