# Generated by Django 5.1.7 on 2025-03-29 18:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0005_faction_rank'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='factionlist',
            name='rank',
        ),
    ]
