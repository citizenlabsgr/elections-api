# Generated by Django 2.2.6 on 2019-10-20 14:01

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("elections", "0031_auto_20191020_0921")]

    operations = [
        migrations.AddField(
            model_name="ballotwebsite",
            name="data",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                editable=False, null=True
            ),
        )
    ]
