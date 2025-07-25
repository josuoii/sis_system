# Generated by Django 4.2.11 on 2025-06-26 17:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('intervention', '0007_alter_chatmessage_sender'),
    ]

    operations = [
        migrations.CreateModel(
            name='MBTIQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('dichotomy', models.CharField(choices=[('EI', 'Extraversion/Introversion'), ('SN', 'Sensing/Intuition'), ('TF', 'Thinking/Feeling'), ('JP', 'Judging/Perceiving')], max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='MBTIAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(choices=[('A', 'First option'), ('B', 'Second option')], max_length=1)),
                ('answered_at', models.DateTimeField(auto_now=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='intervention.mbtiquestion')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'question')},
            },
        ),
    ]
