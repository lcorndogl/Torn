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
        faction_ids = FactionList.objects.values_list(
            'faction_id', flat=True).distinct()

        for faction_id in faction_ids:
            url = f'https://api.torn.com/faction/{faction_id}?selections=basic&key={API_KEY}'
            self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
            response = requests.get(url)

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch data for faction ID {faction_id}. Status code: {response.status_code}'))
                continue

            data = response.json()
            self.stdout.write(self.style.NOTICE(
                f'Response data for faction ID {faction_id}: {data}'))

            if 'members' in data:
                members = data['members']

                # Fetch all existing users in a single query
                existing_user_ids = set(UserList.objects.filter(
                    user_id__in=members.keys()).values_list('user_id', flat=True))

                # Separate new and existing users
                new_users = [
                    UserList(user_id=member_id, game_name=member_data['name'])
                    for member_id, member_data in members.items()
                    if int(member_id) not in existing_user_ids
                ]

                user_records = [
                    UserRecord(
                        user_id_id=member_id,  # Use the ID directly to avoid additional queries
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
                        current_faction_id=faction_id,
                    )
                    for member_id, member_data in members.items()
                ]

                # Bulk create new users
                if new_users:
                    UserList.objects.bulk_create(
                        new_users, ignore_conflicts=True)
                    self.stdout.write(self.style.SUCCESS(
                        f'Created {len(new_users)} new users'))

                # Bulk create user records
                UserRecord.objects.bulk_create(user_records)
                self.stdout.write(self.style.SUCCESS(
                    f'Inserted {len(user_records)} user records for faction ID {faction_id}'))
