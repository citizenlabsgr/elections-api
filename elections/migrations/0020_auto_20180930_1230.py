# Generated by Django 2.0.8 on 2018-09-30 16:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("elections", "0019_auto_20180915_1725")]

    operations = [
        migrations.RenameField(
            model_name="ballotwebsite",
            old_name="last_fetch_with_precent",
            new_name="last_fetch_with_precinct",
        )
    ]
