# Generated by Django 2.0.8 on 2018-09-30 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("elections", "0020_auto_20180930_1230")]

    operations = [
        migrations.AddField(
            model_name="party",
            name="color",
            field=models.CharField(blank=True, max_length=7),
        )
    ]
