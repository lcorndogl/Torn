# Generated by Django 5.1.7 on 2025-05-21 17:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('faction', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserList',
            fields=[
                ('user_id', models.IntegerField(primary_key=True, serialize=False)),
                ('game_name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['game_name'],
            },
        ),
        migrations.CreateModel(
            name='UserRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('level', models.IntegerField()),
                ('days_in_faction', models.IntegerField()),
                ('last_action_status', models.CharField(max_length=255)),
                ('last_action_timestamp', models.IntegerField()),
                ('last_action_relative', models.CharField(max_length=255)),
                ('status_description', models.CharField(max_length=255)),
                ('status_details', models.CharField(blank=True, max_length=255)),
                ('status_state', models.CharField(max_length=255)),
                ('status_color', models.CharField(max_length=50)),
                ('status_until', models.IntegerField()),
                ('position', models.CharField(max_length=255)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('current_faction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='faction.factionlist', to_field='faction_id')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userlist')),
            ],
        ),
        migrations.CreateModel(
            name='UserOrganisedCrimeCPR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_cpr', models.IntegerField(blank=True, null=True)),
                ('organised_crime_role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='faction.organisedcrimerole')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userlist')),
            ],
            options={
                'unique_together': {('user', 'organised_crime_role')},
            },
        ),
    ]
