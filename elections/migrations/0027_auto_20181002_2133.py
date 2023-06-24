# Generated by Django 2.0.9 on 2018-10-03 01:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0026_auto_20181001_2338")]

    operations = [
        migrations.RemoveField(model_name="ballot", name="website"),
        migrations.AddField(
            model_name="ballotwebsite",
            name="ballot",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="websites",
                to="elections.Ballot",
            ),
        ),
    ]
