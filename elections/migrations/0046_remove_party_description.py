# Generated by Django 3.0 on 2019-12-29 23:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("elections", "0045_auto_20191122_2102")]

    operations = [migrations.RemoveField(model_name="party", name="description")]
