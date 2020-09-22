# Generated by Django 3.0.10 on 2020-09-22 22:59

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0054_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationstatus',
            name='dropbox_location',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
