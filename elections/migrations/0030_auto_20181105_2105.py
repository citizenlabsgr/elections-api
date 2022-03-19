# Generated by Django 2.1.2 on 2018-11-06 02:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("elections", "0029_auto_20181009_1849")]

    operations = [
        migrations.AlterModelOptions(name="candidate", options={"ordering": ["name"]}),
        migrations.AlterModelOptions(
            name="party",
            options={"ordering": ["name"], "verbose_name_plural": "Parties"},
        ),
        migrations.AlterModelOptions(
            name="position", options={"ordering": ["name", "seats"]}
        ),
        migrations.AlterModelOptions(name="proposal", options={"ordering": ["name"]}),
    ]
