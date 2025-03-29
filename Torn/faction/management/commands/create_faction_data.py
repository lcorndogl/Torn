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
        base_url = 'https://api.torn.com/v2/torn/factionhof'
        headers = {
            'accept': 'application/json',
            'Authorization': f'ApiKey {API_KEY}'
        }
        offset = 0
        limit = 100
        all_factions = []

        while True:
            url = f'{base_url}?limit={limit}&offset={offset}&cat=rank'
            self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch data. Status code: {response.status_code}'))
                break

            data = response.json()
            factions = [
                faction for faction in data.get('factionhof', [])
                if faction.get('rank') in ['Platinum II', 'Platinum III'] or 'Diamond' in faction.get('rank', '')
            ]

            if not factions:
                self.stdout.write(self.style.NOTICE('No more factions found.'))
                break

            all_factions.extend(factions)
            offset += limit

        if not all_factions:
            self.stdout.write(self.style.WARNING(
                'No factions found with rank Platinum II or higher.'))
            return

        # Get existing faction IDs from the database
        existing_faction_ids = set(
            FactionList.objects.values_list('faction_id', flat=True))

        # Filter out factions that are already in the database
        new_factions = [
            FactionList(
                faction_id=faction_data['id'],
                name=faction_data['name'],
                tag=faction_data.get('tag', '')
            )
            for faction_data in all_factions
            if faction_data['id'] not in existing_faction_ids
        ]

        # Bulk insert new factions
        if new_factions:
            FactionList.objects.bulk_create(new_factions)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully added {len(new_factions)} new factions to the database.'
            ))
        else:
            self.stdout.write(self.style.NOTICE('No new factions to add.'))
