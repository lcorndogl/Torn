# Generated by Django 5.1.6 on 2025-03-25 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
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
            ],
        ),
    ]
