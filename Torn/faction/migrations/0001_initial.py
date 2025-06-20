# Generated by Django 5.1.7 on 2025-05-21 17:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FactionList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faction_id', models.IntegerField(unique=True)),
                ('name', models.CharField(max_length=255)),
                ('tag', models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='OrganisedCrimeRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crime_name', models.CharField(max_length=255)),
                ('level', models.CharField(max_length=50)),
                ('role', models.CharField(max_length=50)),
                ('required_cpr', models.IntegerField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Faction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('respect', models.IntegerField()),
                ('rank', models.CharField(blank=True, max_length=50, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('faction_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='faction.factionlist', to_field='faction_id')),
            ],
        ),
    ]
