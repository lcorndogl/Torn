import requests
import environ
from django.core.management.base import BaseCommand
from faction.models import Faction, FactionList
from users.models import UserList, UserRecord

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

API_KEY = env('API_KEY')

class Command(BaseCommand):
    help = 'Update user data for all faction members'

    def handle(self, *args, **kwargs):
        faction_ids = FactionList.objects.values_list('faction_id', flat=True).distinct()
        
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
            if 'members' in data:
                members = data['members']
                for member_id, member_data in members.items():
                    user_list, created = UserList.objects.get_or_create(
                        user_id=member_id,
                        defaults={'game_name': member_data['name']}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created new user {user_list.game_name}'))

                    UserRecord.objects.create(
                        user_id=user_list,
                        name=member_data['name'],
                        level=member_data['level'],
                        days_in_faction=member_data['days_in_faction'],
                        last_action_status=member_data['last_action']['status'],
                        last_action_timestamp=member_data['last_action']['timestamp'],
                        last_action_relative=member_data['last_action']['relative'],
                        status_description=member_data['status']['description'],
                        status_details=member_data['status'].get('details', ''),
                        status_state=member_data['status']['state'],
                        status_color=member_data['status']['color'],
                        status_until=member_data['status']['until'],
                        position=member_data['position'],
                        current_faction_id=faction_id,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created user record for {user_list.game_name}'))