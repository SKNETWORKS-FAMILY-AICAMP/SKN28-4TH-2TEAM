from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatmessage",
            name="warning",
            field=models.TextField(blank=True),
        ),
    ]
