from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("health_data", "0023_reportimage_ai_fields_checkupresultvalue_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="checkuporphanfield",
            name="item_code",
            field=models.CharField(
                blank=True,
                help_text="报告原文中的项目编码快照。",
                max_length=64,
                verbose_name="原始项目编码",
            ),
        ),
        migrations.AddField(
            model_name="checkupresultvalue",
            name="item_code",
            field=models.CharField(
                blank=True,
                help_text="报告原文中的项目编码快照。",
                max_length=64,
                verbose_name="原始项目编码",
            ),
        ),
        migrations.AddField(
            model_name="reportimage",
            name="ai_sync_warnings",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="AI 结果与归档信息冲突时的告警与处理状态。",
                verbose_name="AI同步告警",
            ),
        ),
    ]
