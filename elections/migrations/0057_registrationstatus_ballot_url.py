# Generated by Django 3.1.13 on 2021-10-20 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0056_fix_deprecations'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationstatus',
            name='ballot_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]