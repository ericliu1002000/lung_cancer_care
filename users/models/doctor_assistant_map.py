from django.db import models

from users.models.base import TimeStampedModel


class DoctorAssistantMap(TimeStampedModel):
    """
    【业务说明】医生与助理的多对多映射表，便于分工管理。
    【用法】在运营后台绑定或解绑助理，系统自动记录创建时间。
    【使用示例】`DoctorAssistantMap.objects.create(doctor=doc, assistant=asst)`。
    【参数】doctor、assistant 外键。
    【返回值】Model。
    """

    doctor = models.ForeignKey(
        "users.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="doctor_assistant_links",
        verbose_name="医生",
        help_text="【业务说明】被服务的医生；【用法】必填；【示例】DoctorProfile#2；【参数】外键；【返回值】DoctorProfile",
    )
    assistant = models.ForeignKey(
        "users.AssistantProfile",
        on_delete=models.CASCADE,
        related_name="assistant_doctor_links",
        verbose_name="助理",
        help_text="【业务说明】提供服务的助理；【用法】必填；【示例】AssistantProfile#6；【参数】外键；【返回值】AssistantProfile",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "assistant"], name="uq_doctor_assistant_pair"
            )
        ]
        verbose_name = "Doctor Assistant Mapping"
        verbose_name_plural = "Doctor Assistant Mapping"

    def __str__(self) -> str:
        """
        【业务说明】输出映射对，便于调试。
        【用法】`str(mapping)`。
        【参数】self。
        【返回值】str，如“Doctor#1-Assistant#3”。
        【使用示例】日志。
        """

        return f"Doctor#{self.doctor_id}-Assistant#{self.assistant_id}"
