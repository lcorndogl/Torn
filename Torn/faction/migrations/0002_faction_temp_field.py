# Generated by Django 5.1.7 on 2025-03-29 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='faction',
            name='temp_field',
            field=models.CharField(default='temp', max_length=10),
        ),
    ]
