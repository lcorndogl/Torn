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

        factions_to_create = []
        user_records_to_create = []

        for faction_id in faction_ids:
            # Check if we need to delay to respect the rate limit
            current_time = time.time()
            while call_timestamps and current_time - call_timestamps[0] > 60:
                call_timestamps.popleft()  # Remove timestamps older than 60 seconds

            if len(call_timestamps) >= 40:
                delay = 65 - (current_time - call_timestamps[0])
                self.stdout.write(self.style.NOTICE(
                    f'Rate limit reached. Waiting for {delay:.2f} seconds...'))
                time.sleep(delay)
                call_timestamps.popleft()

            # Make the API call
            url = f'https://api.torn.com/faction/{faction_id}?selections=basic&key={API_KEY}'
            # self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
            response = requests.get(url)
            # Record the timestamp of this call
            call_timestamps.append(time.time())

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch data for faction ID {faction_id}. Status code: {response.status_code}'))
                continue

            data = response.json()
            # self.stdout.write(self.style.NOTICE(
            #     f'Response data for faction ID {faction_id}: {data}'))

            # Check if the faction data exists
            if 'ID' in data:
                faction_data = data
                faction_list = FactionList.objects.get(
                    faction_id=faction_data['ID']
                )
                
                # Construct the rank string
                rank_data = faction_data.get('rank', {})
                rank_name = rank_data.get('name', '')
                rank_division = rank_data.get('division', 0)
                rank = rank_name + (' ' + 'I' * rank_division if rank_division > 0 else '')

                # Collect faction data for bulk creation
                factions_to_create.append(Faction(
                    faction_id=faction_list,
                    respect=faction_data['respect'],
                    rank=rank
                ))

                # Process members data
                if 'members' in faction_data:
                    for member_id, member_data in faction_data['members'].items():
                        # Use member_id as user_id if 'user_id' is missing
                        user_id = member_data.get('user_id', member_id)

                        # Ensure UserList exists
                        user_list, created = UserList.objects.get_or_create(
                            user_id=user_id,
                            defaults={'game_name': member_data['name']}
                        )

                        # Collect user record data for bulk creation
                        user_records_to_create.append(UserRecord(
                            user_id=user_list,
                            name=member_data['name'],
                            level=member_data['level'],
                            days_in_faction=member_data['days_in_faction'],
                            last_action_status=member_data['last_action']['status'],
                            last_action_timestamp=member_data['last_action']['timestamp'],
                            last_action_relative=member_data['last_action']['relative'],
                            status_description=member_data['status']['description'],
                            status_details=member_data['status'].get(
                                'details', ''),
                            status_state=member_data['status']['state'],
                            status_color=member_data['status']['color'],
                            status_until=member_data['status']['until'],
                            position=member_data['position'],
                            current_faction=faction_list
                        ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch faction data for faction ID {faction_id}'))

        # Bulk create factions and user records
        if factions_to_create:
            Faction.objects.bulk_create(factions_to_create)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully added {len(factions_to_create)} factions in bulk.'
            ))

        if user_records_to_create:
            UserRecord.objects.bulk_create(user_records_to_create)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully added {len(user_records_to_create)} user records in bulk.'
            ))
