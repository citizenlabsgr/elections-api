# Generated by Django 3.2.15 on 2022-09-22 22:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0059_registrationstatus_dropbox_locations"),
    ]

    operations = [
        migrations.AddField(
            model_name="position",
            name="described",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="proposal",
            name="described",
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
