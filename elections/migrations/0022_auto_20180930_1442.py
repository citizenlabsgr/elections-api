# Generated by Django 2.0.8 on 2018-09-30 18:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0021_party_color")]

    operations = [
        migrations.AlterField(
            model_name="party",
            name="color",
            field=models.CharField(blank=True, editable=False, max_length=7),
        ),
        migrations.AlterField(
            model_name="party",
            name="name",
            field=models.CharField(editable=False, max_length=50, unique=True),
        ),
    ]
