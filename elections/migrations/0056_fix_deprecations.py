# Generated by Django 3.1.6 on 2021-05-22 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0055_registrationstatus_dropbox_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ballotwebsite',
            name='data',
            field=models.JSONField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='ballotwebsite',
            name='valid',
            field=models.BooleanField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='registrationstatus',
            name='dropbox_location',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='registrationstatus',
            name='polling_location',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
