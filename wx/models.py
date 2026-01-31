from django.db import models
from users.models.base import TimeStampedModel

class MessageTemplate(TimeStampedModel):
    """
    【业务说明】用于存放系统发送给用户的各类文案，支持动态变量。
    【用法】通过 code 查找模板，使用 format 渲染变量。
    【使用示例】`MessageTemplate.objects.create(code="welcome", content="你好，{name}")`。
    """
    
    code = models.CharField(
        "模版编码",
        max_length=50,
        unique=True,
        db_index=True,
        help_text="【程序员看】唯一标识，代码中通过此字段获取文案。例如：bind_success_self"
    )
    title = models.CharField(
        "模版名称",
        max_length=100,
        help_text="【运营看】描述这个文案是用在哪里的。"
    )
    content = models.TextField(
        "文案内容",
        help_text="支持变量替换。例如：你好，{name}。请确保变量名与开发约定一致。"
    )
    available_vars = models.CharField(
        "可用变量说明",
        max_length=255,
        blank=True,
        help_text="备注提示，例如：{name}=患者姓名, {doctor}=医生姓名"
    )
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        verbose_name = "微信消息文案库"
        verbose_name_plural = "微信消息文案库"

    def __str__(self):
        return f"{self.title} ({self.code})"


class SendMessageLog(TimeStampedModel):
    """微信模板消息发送日志。"""

    class Channel(models.TextChoices):
        WECHAT = "wechat", "微信"
        WATCH = "watch", "手表"

    class Scene(models.TextChoices):
        DAILY_TASK_CREATED = "daily_task_created", "每日任务生成"
        DAILY_TASK_REMINDER = "daily_task_reminder", "每日任务提醒"

    patient = models.ForeignKey(
        "users.PatientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wx_message_logs",
        verbose_name="患者",
    )
    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wx_message_logs",
        verbose_name="接收用户",
    )
    openid = models.CharField(
        "OpenID",
        max_length=64,
        blank=True,
        db_index=True,
        help_text="发送时使用的 OpenID 快照。",
    )
    channel = models.CharField(
        "发送渠道",
        max_length=20,
        choices=Channel.choices,
        default=Channel.WECHAT,
        db_index=True,
    )
    scene = models.CharField(
        "消息场景",
        max_length=50,
        choices=Scene.choices,
        db_index=True,
    )
    biz_date = models.DateField(
        "业务日期",
        null=True,
        blank=True,
        db_index=True,
        help_text="关联的业务日期，例如任务日期。",
    )
    content = models.TextField("消息内容")
    payload = models.JSONField("发送载荷", default=dict, blank=True)
    is_success = models.BooleanField("是否成功", default=True)
    error_message = models.CharField("错误信息", max_length=255, blank=True)

    class Meta:
        db_table = "wx_send_message_logs"
        verbose_name = "微信消息发送日志"
        verbose_name_plural = "微信消息发送日志"
        indexes = [
            models.Index(fields=["scene", "biz_date"], name="idx_wx_msg_scene_date"),
            models.Index(fields=["patient", "biz_date"], name="idx_wx_msg_patient_date"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.scene}({self.biz_date}) -> {self.openid}"
