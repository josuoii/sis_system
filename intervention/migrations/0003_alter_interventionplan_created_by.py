# Generated by Django 5.2.1 on 2025-06-24 10:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intervention', '0002_class_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interventionplan',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_interventions', to='intervention.teacher'),
        ),
    ]
