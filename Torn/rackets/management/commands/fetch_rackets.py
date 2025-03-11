import requests
from django.core.management.base import BaseCommand
from racket.models import Rackets
from env import API_KEY  # Import the API key from env.py
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetch rackets data from the API and populate the Rackets model'

    def handle(self, *args, **kwargs):
        url = f'https://api.torn.com/torn/?selections=rackets&key={API_KEY}&comment=RacketCheck'
        response = requests.get(url)
        data = response.json()

        for code, item in data['rackets'].items():
            created = datetime.fromtimestamp(item['created'])
            changed = datetime.fromtimestamp(item['changed'])
            Rackets.objects.update_or_create(
                territory=code,
                defaults={
                    'name': item['name'],
                    'level': item['level'],
                    'reward': item['reward'],
                    'created': created,
                    'changed': changed,
                    'faction': item['faction'],
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully fetched and populated Rackets data'))