# Generated by Django 5.1.6 on 2025-04-30 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faction', '0008_rename_organisedcrimesroles_organisedcrimerole'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisedcrimerole',
            name='crime_name',
            field=models.CharField(default='a', max_length=255),
            preserve_default=False,
        ),
    ]
