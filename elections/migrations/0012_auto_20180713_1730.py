# Generated by Django 2.0.7 on 2018-07-13 21:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [('elections', '0011_auto_20180713_1713')]

    operations = [
        migrations.RenameField(
            model_name='precinct', old_name='precinct', new_name='number'
        ),
    ]
