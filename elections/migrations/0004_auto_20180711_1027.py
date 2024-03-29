# Generated by Django 2.0.7 on 2018-07-11 14:27

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("elections", "0003_auto_20180711_0844")]

    operations = [
        migrations.AlterModelOptions(name="poll", options={"ordering": ["mi_sos_id"]}),
        migrations.AlterUniqueTogether(
            name="poll",
            unique_together={
                ("county", "jurisdiction", "ward", "precinct", "mi_sos_id")
            },
        ),
    ]
