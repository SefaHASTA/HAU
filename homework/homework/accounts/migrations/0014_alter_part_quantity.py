# Generated by Django 5.2.1 on 2025-05-10 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_aircrafttype_alter_part_quantity_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='part',
            name='quantity',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
