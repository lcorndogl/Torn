# Generated by Django 5.1.7 on 2025-03-11 21:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Rackets',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('territory', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('level', models.IntegerField()),
                ('reward', models.IntegerField()),
                ('created', models.DateTimeField()),
                ('changed', models.DateTimeField()),
                ('faction', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
