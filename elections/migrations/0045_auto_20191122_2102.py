# Generated by Django 2.2.7 on 2019-11-23 02:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('elections', '0044_remove_ballotwebsite_refetch_weight')]

    operations = [
        migrations.AlterModelOptions(name='election', options={'ordering': ['-date']}),
        migrations.AddField(
            model_name='registrationstatus',
            name='absentee',
            field=models.BooleanField(default=False),
        ),
    ]