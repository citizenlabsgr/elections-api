# Generated by Django 3.2.15 on 2022-09-24 23:07

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0062_districtcategory_described"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="candidate",
            options={"ordering": ["party__name", "name"]},
        ),
    ]
