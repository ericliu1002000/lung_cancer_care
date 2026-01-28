from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("health_data", "0017_alter_clinicalevent_archiver_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportimage",
            name="health_metric",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="report_images",
                to="health_data.healthmetric",
                verbose_name="关联指标",
                help_text="归档后关联的指标记录（复查场景）。",
            ),
        ),
    ]
