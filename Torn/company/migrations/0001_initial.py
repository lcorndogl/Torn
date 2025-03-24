# Generated by Django 5.1.6 on 2025-03-24 20:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('company_id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('position', models.CharField(max_length=255)),
                ('manual_labour', models.IntegerField()),
                ('intelligence', models.IntegerField()),
                ('endurance', models.IntegerField()),
                ('effectiveness_working_stats', models.IntegerField()),
                ('effectiveness_settled_in', models.IntegerField()),
                ('effectiveness_merits', models.IntegerField(default=0)),
                ('effectiveness_director_education', models.IntegerField()),
                ('effectiveness_management', models.IntegerField()),
                ('effectiveness_inactivity', models.IntegerField()),
                ('effectiveness_total', models.IntegerField()),
                ('last_action_status', models.CharField(max_length=255)),
                ('last_action_timestamp', models.DateTimeField()),
                ('last_action_relative', models.CharField(max_length=255)),
                ('status_description', models.CharField(max_length=255)),
                ('status_state', models.CharField(max_length=255)),
                ('status_until', models.DateTimeField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.company')),
            ],
            options={
                'unique_together': {('company', 'employee_id')},
            },
        ),
    ]
