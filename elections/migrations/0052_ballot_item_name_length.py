# Generated by Django 3.0.9 on 2020-08-20 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("elections", "0051_registration_status_dates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="position",
            name="name",
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name="proposal",
            name="name",
            field=models.CharField(max_length=500),
        ),
    ]
