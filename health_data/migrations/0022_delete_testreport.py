from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("health_data", "0021_alter_healthmetric_metric_type"),
    ]

    operations = [
        migrations.DeleteModel(
            name="TestReport",
        ),
    ]
