import requests
import environ
import time
from collections import deque
from django.core.management.base import BaseCommand
from faction.models import Faction, FactionList
from users.models import UserList, UserRecord

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

API_KEY = env('API_KEY')


class Command(BaseCommand):
    help = 'Fetch faction data from the Torn API and add a new record for each unique faction ID'

    def handle(self, *args, **kwargs):
        faction_ids = FactionList.objects.values_list(
            'faction_id', flat=True).distinct()
        call_timestamps = deque()  # Track timestamps of API calls

        for faction_id in faction_ids:
            # Check if we need to delay to respect the rate limit
            current_time = time.time()
            while call_timestamps and current_time - call_timestamps[0] > 60:
                call_timestamps.popleft()  # Remove timestamps older than 60 seconds

            if len(call_timestamps) >= 60:
                delay = 65 - (current_time - call_timestamps[0])
                self.stdout.write(self.style.NOTICE(
                    f'Rate limit reached. Waiting for {delay:.2f} seconds...'))
                time.sleep(delay)
                call_timestamps.popleft()

            # Make the API call
            url = f'https://api.torn.com/faction/{faction_id}?selections=basic&key={API_KEY}'
            self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
            response = requests.get(url)
            # Record the timestamp of this call
            call_timestamps.append(time.time())

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch data for faction ID {faction_id}. Status code: {response.status_code}'))
                continue

            data = response.json()
            self.stdout.write(self.style.NOTICE(
                f'Response data for faction ID {faction_id}: {data}'))

            # Check if the faction data exists
            if 'ID' in data:
                faction_data = data
                Faction.objects.create(
                    faction_id=FactionList.objects.get(
                        faction_id=faction_data['ID']),
                    respect=faction_data['respect']
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully added new faction {faction_data["name"]}'))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch faction data for faction ID {faction_id}'))
