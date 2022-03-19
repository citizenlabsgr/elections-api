# Generated by Django 3.0.7 on 2020-06-05 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("elections", "0047_registrationstatus_recently_moved"),
    ]

    operations = [
        migrations.AddField(
            model_name="position",
            name="section",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name="position",
            unique_together={
                ("election", "section", "district", "name", "term", "seats")
            },
        ),
    ]
