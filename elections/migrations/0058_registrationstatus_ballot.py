# Generated by Django 3.1.13 on 2021-10-22 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("elections", "0057_registrationstatus_ballot_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="registrationstatus",
            name="ballot",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="registrationstatus",
            name="absentee",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="registrationstatus",
            name="recently_moved",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
