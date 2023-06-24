# Generated by Django 2.0.8 on 2018-08-04 16:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0015_auto_20180731_2235")]

    operations = [
        migrations.RemoveField(model_name="position", name="precinct"),
        migrations.RemoveField(model_name="proposal", name="precinct"),
        migrations.AddField(
            model_name="position",
            name="precincts",
            field=models.ManyToManyField(to="elections.Precinct"),
        ),
        migrations.AddField(
            model_name="proposal",
            name="precincts",
            field=models.ManyToManyField(to="elections.Precinct"),
        ),
        migrations.AlterField(
            model_name="position",
            name="district",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.District",
            ),
        ),
        migrations.AlterField(
            model_name="position", name="name", field=models.CharField(max_length=200)
        ),
        migrations.AlterField(
            model_name="proposal",
            name="district",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="elections.District",
            ),
        ),
        migrations.AlterField(
            model_name="proposal", name="name", field=models.CharField(max_length=200)
        ),
    ]
