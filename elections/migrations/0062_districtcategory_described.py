# Generated by Django 3.2.15 on 2022-09-23 11:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0061_proposal_remove_described"),
    ]

    operations = [
        migrations.AddField(
            model_name="districtcategory",
            name="described",
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
