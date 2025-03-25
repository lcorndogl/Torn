import requests
import environ
from django.core.management.base import BaseCommand
from faction.models import FactionList

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

API_KEY = env('API_KEY')

class Command(BaseCommand):
    help = 'Fetch faction data from the Torn API and insert it into the database'

    def handle(self, *args, **kwargs):
        url = f'https://api.torn.com/faction/44758?selections=basic&key={API_KEY}'
        self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
        response = requests.get(url)
        
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f'Failed to fetch data. Status code: {response.status_code}'))
            return
        
        data = response.json()
        self.stdout.write(self.style.NOTICE(f'Response data: {data}'))

        # Check if the faction data exists
        if 'ID' in data:
            faction_data = data
            faction, created = FactionList.objects.update_or_create(
                faction_id=faction_data['ID'],
                defaults={
                    'name': faction_data['name'],
                    'tag': faction_data['tag']
                }
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully {"created" if created else "updated"} faction {faction.name}'))
        else:
            self.stdout.write(self.style.ERROR('Failed to fetch faction data'))