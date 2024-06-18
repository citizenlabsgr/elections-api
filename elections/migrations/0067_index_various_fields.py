# Generated by Django 5.0b1 on 2024-06-18 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("elections", "0066_index_election_active"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ballotwebsite",
            name="mvic_election_id",
            field=models.PositiveIntegerField(
                db_index=True, verbose_name="MVIC Election ID"
            ),
        ),
        migrations.AlterField(
            model_name="ballotwebsite",
            name="mvic_precinct_id",
            field=models.PositiveIntegerField(
                db_index=True, verbose_name="MVIC Precinct ID"
            ),
        ),
        migrations.AlterField(
            model_name="district",
            name="name",
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="district",
            name="population",
            field=models.PositiveIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="districtcategory",
            name="rank",
            field=models.IntegerField(
                db_index=True, default=0, help_text="Controls ballot item ordering"
            ),
        ),
        migrations.AlterField(
            model_name="election",
            name="date",
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name="election",
            name="mvic_id",
            field=models.PositiveIntegerField(db_index=True, verbose_name="MVIC ID"),
        ),
        migrations.AlterField(
            model_name="party",
            name="name",
            field=models.CharField(
                db_index=True, editable=False, max_length=50, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="position",
            name="name",
            field=models.CharField(db_index=True, max_length=500),
        ),
        migrations.AlterField(
            model_name="position",
            name="term",
            field=models.CharField(blank=True, db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="precinct",
            name="number",
            field=models.CharField(blank=True, db_index=True, max_length=3),
        ),
        migrations.AlterField(
            model_name="precinct",
            name="ward",
            field=models.CharField(blank=True, db_index=True, max_length=2),
        ),
        migrations.AlterField(
            model_name="proposal",
            name="name",
            field=models.CharField(db_index=True, max_length=500),
        ),
    ]
