# Generated by Django 2.2.6 on 2019-11-03 12:50

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("elections", "0042_auto_20191102_1929")]

    operations = [
        migrations.AddField(
            model_name="registrationstatus",
            name="polling_location",
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        )
    ]
