# Generated by Django 2.0.7 on 2018-07-03 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("elections", "0003_auto_20180702_2116")]

    operations = [
        migrations.AddField(
            model_name="district",
            name="population",
            field=models.PositiveIntegerField(blank=True, null=True),
        )
    ]