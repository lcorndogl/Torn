import requests
import environ
from django.core.management.base import BaseCommand
from faction.models import FactionList

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

API_KEY = env('API_KEY')


class Command(BaseCommand):
    help = 'Fetch faction data from the Torn API and insert factions ranked Platinum II or higher into the database'

    def handle(self, *args, **kwargs):
        url = 'https://api.torn.com/v2/torn/factionhof?limit=100&cat=rank'
        headers = {
            'accept': 'application/json',
            'Authorization': f'ApiKey {API_KEY}'
        }
        self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(
                f'Failed to fetch data. Status code: {response.status_code}'))
            return

        data = response.json()
        self.stdout.write(self.style.NOTICE(f'Response data: {data}'))

        # Filter factions ranked Platinum II or higher
        valid_ranks = ['Platinum II', 'Platinum I',
                       'Diamond III', 'Diamond II', 'Diamond I']
        factions = [
            faction for faction in data.get('factionhof', [])
            if faction.get('rank') in valid_ranks
        ]

        if not factions:
            self.stdout.write(self.style.WARNING(
                'No factions found with rank Platinum II or higher.'))
            return

        # Insert or update factions in the database
        for faction_data in factions:
            faction, created = FactionList.objects.update_or_create(
                faction_id=faction_data['id'],
                defaults={
                    'name': faction_data['name'],
                    # Use .get() to handle missing 'tag'
                    'tag': faction_data.get('tag', '')
                }
            )
            self.stdout.write(self.style.SUCCESS(
                f'Successfully {"created" if created else "updated"} faction {faction.name} with rank {faction_data["rank"]}'
            ))
