# Generated by Django 3.2.18 on 2023-03-14 01:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("elections", "0063_candidate_order_by_party"),
    ]

    operations = [
        migrations.AddField(
            model_name="position",
            name="ballots",
            field=models.ManyToManyField(to="elections.Ballot"),
        ),
        migrations.AddField(
            model_name="proposal",
            name="ballots",
            field=models.ManyToManyField(to="elections.Ballot"),
        ),
        migrations.AlterField(
            model_name="ballot",
            name="website",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ballot",
                to="elections.ballotwebsite",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="ballot",
            unique_together=set(),
        ),
    ]
