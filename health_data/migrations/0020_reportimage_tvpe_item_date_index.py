from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("health_data", "0018_reportimage_health_metric"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="reportimage",
            index=models.Index(
                fields=["record_type", "checkup_item", "report_date"],
                name="idx_rptimg_type_item_date",
            ),
        ),
    ]
