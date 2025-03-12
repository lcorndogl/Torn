import requests
import environ
from django.core.management.base import BaseCommand
from racket.models import Racket, Territory
from datetime import datetime
from django.utils import timezone

# Initialize environment variables
env = environ.Env()
environ.Env.read_env('/media/michael/HDD/torn/.env')  # Explicitly load the .env file

# env = environ.Env()
API_KEY = env('API_KEY')

class Command(BaseCommand):
    help = 'Fetch rackets data from the API and populate the Racket model'

    def handle(self, *args, **kwargs):
        url = f'https://api.torn.com/torn/?selections=rackets&key={API_KEY}&comment=RacketCheck'
        response = requests.get(url)
        data = response.json()

        for code, item in data['rackets'].items():
            created = timezone.make_aware(datetime.fromtimestamp(item['created']))
            changed = timezone.make_aware(datetime.fromtimestamp(item['changed']))
            territory, _ = Territory.objects.get_or_create(
                code=code,
                defaults={'name': item['name']}  # Use name field
            )
            Racket.objects.create(
                territory=territory,
                name=item['name'],
                level=item['level'],
                reward=item['reward'],
                created=created,
                changed=changed,
                faction=item['faction'],
            )

        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        self.stdout.write(self.style.SUCCESS(f'Successfully fetched and populated Racket data at {timestamp}'))