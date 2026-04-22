from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("health_data", "0024_reportimage_ai_sync_warnings_and_item_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportimage",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, help_text="最后一次人工修订保存时间。", null=True, verbose_name="最后修订时间"),
        ),
        migrations.AddField(
            model_name="reportimage",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                help_text="最后一次人工修订该图片结构化结果的后台账号。",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_report_images",
                to=settings.AUTH_USER_MODEL,
                verbose_name="最后修订人",
            ),
        ),
        migrations.AddField(
            model_name="reportimage",
            name="reviewed_structured_json",
            field=models.JSONField(blank=True, help_text="后台人工修订后当前生效的结构化 JSON。", null=True, verbose_name="人工修订结构化结果"),
        ),
    ]
