# Generated by Django 2.2.6 on 2019-10-20 13:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("elections", "0030_auto_20181105_2105")]

    operations = [
        migrations.RenameField(
            model_name="ballotwebsite", old_name="table_count", new_name="data_count"
        ),
        migrations.AlterField(
            model_name="ballotwebsite",
            name="fetched",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name="ballotwebsite",
            name="mi_sos_html",
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AlterField(
            model_name="ballotwebsite",
            name="parsed",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AlterField(
            model_name="ballotwebsite",
            name="refetch_weight",
            field=models.FloatField(default=1.0, editable=False),
        ),
        migrations.AlterField(
            model_name="ballotwebsite",
            name="valid",
            field=models.NullBooleanField(editable=False),
        ),
        migrations.AlterField(
            model_name="ballotwebsite",
            name="data_count",
            field=models.IntegerField(default=-1, editable=False),
        ),
    ]
