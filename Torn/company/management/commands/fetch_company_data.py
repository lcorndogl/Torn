import requests
import environ
from django.core.management.base import BaseCommand
from company.models import Company, Employee, CurrentEmployee, DailyEmployeeSnapshot
from datetime import datetime, time, timedelta

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

API_KEY = env('API_KEY')


class Command(BaseCommand):
    help = 'Fetch company data from the Torn API and insert it into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force run even before 18:22 UTC; snapshots will be recorded for the previous day'
        )

    def handle(self, *args, **kwargs):
        force_run = kwargs.get('force', False)
        
        # Run once per available key so we can ingest data for both companies if keys differ
        pc_key = env('PC_KEY', default=None)
        keys_to_use = [
            ("PC_KEY", pc_key),
            ("API_KEY", API_KEY),
        ]

        ran_any = False
        now_utc = datetime.utcnow().time()

        for key_type, api_key in keys_to_use:
            if not api_key:
                continue

            ran_any = True
            self.stdout.write(f'Using {key_type} for API requests')

            # Create a normalized timestamp for this fetch (rounded to the minute)
            fetch_time = datetime.now()
            normalized_time = fetch_time.replace(second=0, microsecond=0)
            
            # For Employee model: always use today's date
            employee_created_on = normalized_time
            
            # For DailyEmployeeSnapshot: only create/update snapshot after 18:22 UTC
            snapshot_date = normalized_time.date()
            skip_snapshot = False
            if now_utc < time(18, 22) and not force_run:
                skip_snapshot = True
                # Before 18:22 UTC: update previous day's snapshot with Switzerland info
                snapshot_date = snapshot_date - timedelta(days=1)
                self.stdout.write(self.style.WARNING(
                    f"Current UTC time {now_utc.strftime('%H:%M:%S')} is before 18:22; updating previous day's snapshot ({snapshot_date}) with Switzerland info"
                ))
            elif force_run and now_utc < time(18, 22):
                snapshot_date = snapshot_date - timedelta(days=1)
                self.stdout.write(self.style.WARNING(
                    f"Force flag set before 18:22 UTC; recording snapshots for previous day {snapshot_date}"
                ))
            self.stdout.write(f'Using normalized timestamp: {normalized_time}')
            
            # Fetch the company tied to the key owner (no hardcoded company ID)
            url = f'https://api.torn.com/company/?selections=profile,employees&key={api_key}&comment=FetchCompany'
            response = requests.get(url)
            data = response.json()

            print("Top-level keys:", data.keys())
            print("Company keys:", data.get('company', {}).keys())

            # Check if the company data exists
            if 'company' in data:
                company_data = data['company']
                company, created = Company.objects.get_or_create(
                    company_id=company_data['ID'],
                    defaults={'name': company_data['name']}
                )
            else:
                self.stdout.write(self.style.WARNING('No company data found in the response; aborting fetch for this key'))
                continue

            # Check if the employees data exists
            if 'company_employees' in data and data['company_employees']:
                wage_count = 0
                total_employees = len(data['company_employees'])
                
                # Remove existing CurrentEmployee records for this company
                deleted_count = CurrentEmployee.objects.filter(company_id=company_data['ID']).delete()[0]
                self.stdout.write(f'Removed {deleted_count} existing current employee records for company {company_data["ID"]}')
                
                for employee_id, employee_data in data['company_employees'].items():
                    status_until = employee_data['status']['until']
                    if status_until == 0:
                        status_until = None
                    else:
                        status_until = datetime.fromtimestamp(status_until)

                    wage = employee_data.get('wage')
                    if wage is not None:
                        wage_count += 1

                    employee_defaults = {
                        'name': employee_data['name'],
                        'position': employee_data['position'],
                        'wage': wage,  # Will be None if not available
                        'manual_labour': employee_data.get('manual_labor', 0),
                        'intelligence': employee_data.get('intelligence', 0),
                        'endurance': employee_data.get('endurance', 0),
                        'effectiveness_working_stats': employee_data.get('effectiveness', {}).get('working_stats', 0),
                        'effectiveness_settled_in': employee_data.get('effectiveness', {}).get('settled_in', 0),
                        'effectiveness_merits': employee_data.get('effectiveness', {}).get('merits', 0),
                        'effectiveness_director_education': employee_data.get('effectiveness', {}).get('director_education', 0),
                        'effectiveness_management': employee_data.get('effectiveness', {}).get('management', 0),
                        'effectiveness_inactivity': employee_data.get('effectiveness', {}).get('inactivity', 0),
                        'effectiveness_addiction': employee_data.get('effectiveness', {}).get('addiction', 0),
                        'effectiveness_total': employee_data.get('effectiveness', {}).get('total', 0),
                        'last_action_status': employee_data['last_action']['status'],
                        'last_action_timestamp': datetime.fromtimestamp(employee_data['last_action']['timestamp']),
                        'last_action_relative': employee_data['last_action']['relative'],
                        'status_description': employee_data['status']['description'],
                        'status_state': employee_data['status']['state'],
                        'status_until': status_until,
                        'created_on': employee_created_on  # Tie record to the snapshot date
                    }

                    try:
                        Employee.objects.update_or_create(
                            employee_id=employee_id,
                            company=company,
                            defaults=employee_defaults
                        )
                    except Employee.MultipleObjectsReturned:
                        # Multiple rows exist; update the newest without deleting older history
                        dupes_qs = Employee.objects.filter(employee_id=employee_id, company=company).order_by('-created_on')
                        keep = dupes_qs.first()
                        if keep:
                            for field, value in employee_defaults.items():
                                setattr(keep, field, value)
                            keep.save(update_fields=list(employee_defaults.keys()))
                        else:
                            Employee.objects.create(
                                employee_id=employee_id,
                                company=company,
                                **employee_defaults
                            )

                    # Upsert daily snapshot to ensure one record per employee per day
                    # Before 18:22 UTC: only update Switzerland-related fields
                    # After 18:22 UTC or with force: update all fields
                    
                    # Always prepare full defaults
                    snapshot_defaults = {
                        'name': employee_data['name'],
                        'position': employee_data['position'],
                        'wage': wage,
                        'manual_labour': employee_data.get('manual_labor', 0),
                        'intelligence': employee_data.get('intelligence', 0),
                        'endurance': employee_data.get('endurance', 0),
                        'effectiveness_working_stats': employee_data.get('effectiveness', {}).get('working_stats', 0),
                        'effectiveness_settled_in': employee_data.get('effectiveness', {}).get('settled_in', 0),
                        'effectiveness_merits': employee_data.get('effectiveness', {}).get('merits', 0),
                        'effectiveness_director_education': employee_data.get('effectiveness', {}).get('director_education', 0),
                        'effectiveness_management': employee_data.get('effectiveness', {}).get('management', 0),
                        'effectiveness_inactivity': employee_data.get('effectiveness', {}).get('inactivity', 0),
                        'effectiveness_addiction': employee_data.get('effectiveness', {}).get('addiction', 0),
                        'effectiveness_total': employee_data.get('effectiveness', {}).get('total', 0),
                        'last_action_status': employee_data['last_action']['status'],
                        'last_action_timestamp': datetime.fromtimestamp(employee_data['last_action']['timestamp']),
                        'last_action_relative': employee_data['last_action']['relative'],
                        'status_description': employee_data['status']['description'],
                        'status_state': employee_data['status']['state'],
                        'status_until': status_until,
                    }
                    
                    # Get or create snapshot with full defaults
                    snapshot_obj, created = DailyEmployeeSnapshot.objects.get_or_create(
                        company=company,
                        employee_id=employee_id,
                        snapshot_date=snapshot_date,
                        defaults=snapshot_defaults
                    )
                    
                    # If after 18:22 UTC or forced, update all fields
                    if not skip_snapshot:
                        for field, value in snapshot_defaults.items():
                            setattr(snapshot_obj, field, value)
                        snapshot_obj.save()
                    else:
                        # Before 18:22 UTC: only update Switzerland fields
                        status_desc = employee_data['status']['description'].lower()
                        updated = False
                        
                        if 'to switzerland' in status_desc:
                            snapshot_obj.last_travelled_to_switzerland = datetime.fromtimestamp(
                                employee_data['last_action']['timestamp']
                            )
                            updated = True
                        if 'in switzerland' in status_desc:
                            snapshot_obj.in_switzerland = datetime.fromtimestamp(
                                employee_data['last_action']['timestamp']
                            )
                            updated = True
                        if 'from switzerland' in status_desc or 'returning from switzerland' in status_desc:
                            snapshot_obj.returning_from_switzerland = datetime.fromtimestamp(
                                employee_data['last_action']['timestamp']
                            )
                            updated = True
                        
                        if updated:
                            snapshot_obj.save(update_fields=[
                                'last_travelled_to_switzerland',
                                'in_switzerland',
                                'returning_from_switzerland'
                            ])
                    
                    # Create or update CurrentEmployee record
                    CurrentEmployee.objects.update_or_create(
                        user_id=employee_id,
                        company_id=company_data['ID'],
                        defaults={
                            'username': employee_data['name'],
                            'company_name': company_data['name']
                        }
                    )
                
                self.stdout.write(f'Processed {total_employees} employees')
                self.stdout.write(self.style.SUCCESS(f'Updated {total_employees} current employee records'))
                if wage_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'Wage data available for {wage_count}/{total_employees} employees'))
                else:
                    self.stdout.write(self.style.WARNING(f'No wage data available (try using PC_KEY for wage access)'))
            else:
                self.stdout.write(self.style.WARNING('No employees data found in the response; aborting fetch for this key'))
                continue

            self.stdout.write(self.style.SUCCESS(f'Successfully fetched and inserted company data for {company_data["name"]} (key: {key_type})'))

        if not ran_any:
            self.stdout.write(self.style.ERROR('No usable API keys found (PC_KEY and API_KEY are both missing).'))