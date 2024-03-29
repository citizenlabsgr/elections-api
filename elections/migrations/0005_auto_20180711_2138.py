# Generated by Django 2.0.7 on 2018-07-12 01:38

import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0004_auto_20180711_1027")]

    operations = [
        migrations.CreateModel(
            name="BallotWebpage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("mi_sos_election_id", models.PositiveIntegerField()),
                ("mi_sos_precinct_id", models.PositiveIntegerField()),
                ("mi_sos_html", models.TextField(blank=True)),
                ("valid", models.BooleanField(default=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="ballotwebpage",
            unique_together={("mi_sos_election_id", "mi_sos_precinct_id")},
        ),
    ]
