# Generated by Django 2.0.7 on 2018-07-13 02:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0006_auto_20180711_2148")]

    operations = [
        migrations.AddField(
            model_name="ballot",
            name="website",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="elections.BallotWebpage",
            ),
        ),
        migrations.RemoveField(model_name="ballot", name="mi_sos_html"),
        migrations.AlterUniqueTogether(
            name="ballot", unique_together={("election", "precinct")}
        ),
    ]
