import requests
import environ
from django.core.management.base import BaseCommand
from faction.models import Faction

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

API_KEY = env('API_KEY')

class Command(BaseCommand):
    help = 'Fetch faction data from the Torn API and add a new record for each unique faction ID'

    def handle(self, *args, **kwargs):
        faction_ids = Faction.objects.values_list('faction_id', flat=True).distinct()
        
        for faction_id in faction_ids:
            url = f'https://api.torn.com/faction/{faction_id}?selections=basic&key={API_KEY}'
            self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
            response = requests.get(url)
            
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f'Failed to fetch data for faction ID {faction_id}. Status code: {response.status_code}'))
                continue
            
            data = response.json()
            self.stdout.write(self.style.NOTICE(f'Response data for faction ID {faction_id}: {data}'))

            # Check if the faction data exists
            if 'ID' in data:
                faction_data = data
                Faction.objects.create(
                    faction_id=faction_data['ID'],
                    name=faction_data['name'],
                    tag=faction_data['tag'],
                    respect=faction_data['respect']
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully added new faction {faction_data["name"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to fetch faction data for faction ID {faction_id}'))