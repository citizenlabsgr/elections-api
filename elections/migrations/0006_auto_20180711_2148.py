# Generated by Django 2.0.7 on 2018-07-12 01:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("elections", "0005_auto_20180711_2138")]

    operations = [
        migrations.RenameModel(old_name="Poll", new_name="Precinct"),
        migrations.RenameField(
            model_name="ballot", old_name="poll", new_name="precinct"
        ),
        migrations.RenameField(
            model_name="position", old_name="poll", new_name="precinct"
        ),
        migrations.RenameField(
            model_name="proposal", old_name="poll", new_name="precinct"
        ),
        migrations.RenameField(
            model_name="registrationstatus", old_name="poll", new_name="precinct"
        ),
    ]
