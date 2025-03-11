from celery import shared_task
from django.core.management import call_command


@shared_task
def fetch_rackets_task():
    call_command('fetch_rackets')
