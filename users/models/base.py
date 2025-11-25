from django.db import models


class TimeStampedModel(models.Model):
    """
    【业务说明】所有业务实体都需要记录创建与更新时间，便于审计与溯源。
    【用法】继承该抽象类后自动拥有 `created_at` 和 `updated_at` 字段，无需重复定义。
    【使用示例】患者档案、医生档案、工作室等模型均继承本类。
    【参数】无额外参数。
    【返回值】作为抽象基类不直接实例化，仅提供字段。
    """

    created_at = models.DateTimeField(
        "创建时间",
        auto_now_add=True,
        db_index=True,
        help_text="【业务说明】记录数据首次写入时间；【用法】只读字段，自动写入；【示例】2025-01-01 09:00;【参数】无；【返回值】datetime",
    )
    updated_at = models.DateTimeField(
        "更新时间",
        auto_now=True,
        db_index=True,
        help_text="【业务说明】记录最新修改时间，方便比对变更；【用法】ORM 保存时自动更新；【示例】2025-01-02 18:30;【参数】无；【返回值】datetime",
    )

    class Meta:
        abstract = True
