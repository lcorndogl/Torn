import requests
import environ
from django.core.management.base import BaseCommand
from company.models import Company, Employee, CurrentEmployee, DailyEmployeeSnapshot, Sale
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
        swallow_key = env('SWALLOW_KEY', default=None)
        keys_to_use = [
            ("PC_KEY", pc_key),
            ("SWALLOW_KEY", swallow_key),
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
            
            # For DailyEmployeeSnapshot: check if before 18:00 UTC
            snapshot_date = normalized_time.date()
            if now_utc < time(18, 0) and not force_run:
                # Before 18:00 UTC: use yesterday's date for snapshots
                snapshot_date = snapshot_date - timedelta(days=1)
            # If at/after 18:00 UTC: use today's date
            self.stdout.write(f'Using normalized timestamp: {normalized_time}')
            
            # For Stock: check if before 18:00 UTC
            stock_snapshot_date = normalized_time.date()
            if now_utc < time(18, 0) and not force_run:
                # Before 18:00 UTC: use yesterday's date for snapshots
                stock_snapshot_date = stock_snapshot_date - timedelta(days=1)
            # If at/after 18:00 UTC: use today's date
            
            # Fetch the company tied to the key owner (no hardcoded company ID)
            # Try to fetch with stock data; fall back to without stock if it fails
            url = f'https://api.torn.com/company/?selections=profile,employees,stock,detailed&key={api_key}&comment=FetchCompany'
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                # Check if the response indicates an error
                if 'error' in data:
                    raise Exception(data.get('error', {}).get('error', 'Unknown error'))
                self.stdout.write('Fetched company data with stock information')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to fetch with stock data ({e}); retrying without stock'))
                url = f'https://api.torn.com/company/?selections=profile,employees&key={api_key}&comment=FetchCompany'
                response = requests.get(url)
                data = response.json()

            print("Top-level keys:", data.keys())
            print("Company keys:", data.get('company', {}).keys())
            print("Stock data:", data.get('company_stock', {}))
            print("Detailed data:", data.get('company_detailed', {}))

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

            # Process stock data if available
            stock_data = data.get('company_stock', {})
            detailed_data = data.get('company_detailed', {})
            
            if stock_data:
                self.stdout.write(f'Found stock data for {len(stock_data)} item(s)')
                for item_name, stock_info in stock_data.items():
                    # Before 18:00 UTC: skip if record already exists for this date (yesterday)
                    skip_this_product = False
                    if now_utc < time(18, 0) and not force_run:
                        if Sale.objects.filter(
                            company=company,
                            product_name=item_name,
                            snapshot_date=stock_snapshot_date
                        ).exists():
                            skip_this_product = True
                            self.stdout.write(self.style.WARNING(
                                f"Record already exists for {item_name} on {stock_snapshot_date}; skipping"
                            ))
                    
                    if skip_this_product:
                        continue
                    # Calculate created_amount based on yesterday's stock
                    # created = sold_today + (in_stock_today - in_stock_yesterday)
                    sold_today = stock_info.get('sold_amount', 0)
                    in_stock_today = stock_info.get('in_stock', 0)
                    
                    yesterday_date = stock_snapshot_date - timedelta(days=1)
                    yesterday_sales = Sale.objects.filter(
                        company=company,
                        product_name=item_name,
                        snapshot_date=yesterday_date
                    ).first()
                    
                    if yesterday_sales and yesterday_sales.in_stock is not None:
                        in_stock_yesterday = yesterday_sales.in_stock
                        created_amount = sold_today + (in_stock_today - in_stock_yesterday)
                    else:
                        # No yesterday data, can't calculate daily created
                        created_amount = 0
                    
                    # Get or create sales record for this product
                    upgrades = detailed_data.get('upgrades', {})
                    Sale.objects.update_or_create(
                        company=company,
                        snapshot_date=stock_snapshot_date,
                        defaults={
                            'product_name': item_name,
                            'cost': stock_info.get('cost', 0),
                            'rrp': stock_info.get('rrp', 0),
                            'price': stock_info.get('price', 0),
                            'in_stock': in_stock_today,
                            'on_order': stock_info.get('on_order', 0),
                            'created_amount': created_amount,
                            'sold_amount': sold_today,
                            'sold_worth': stock_info.get('sold_worth', 0),
                            'popularity': detailed_data.get('popularity'),
                            'efficiency': detailed_data.get('efficiency'),
                            'environment': detailed_data.get('environment'),
                            'advertising_budget': detailed_data.get('advertising_budget'),
                            'trains_available': detailed_data.get('trains_available'),
                            'company_size': upgrades.get('company_size'),
                            'staffroom_size': upgrades.get('staffroom_size'),
                            'storage_size': upgrades.get('storage_size'),
                            'storage_space': upgrades.get('storage_space'),
                        }
                    )
                    
                self.stdout.write(self.style.SUCCESS(f'Processed {len(stock_data)} stock item(s) for {stock_snapshot_date}'))
            elif detailed_data and not (now_utc < time(18, 0) and not force_run):
                # Even without stock data, record detailed company metrics if available
                upgrades = detailed_data.get('upgrades', {})
                Sale.objects.update_or_create(
                    company=company,
                    snapshot_date=stock_snapshot_date,
                    defaults={
                        'popularity': detailed_data.get('popularity'),
                        'efficiency': detailed_data.get('efficiency'),
                        'environment': detailed_data.get('environment'),
                        'advertising_budget': detailed_data.get('advertising_budget'),
                        'trains_available': detailed_data.get('trains_available'),
                        'company_size': upgrades.get('company_size'),
                        'staffroom_size': upgrades.get('staffroom_size'),
                        'storage_size': upgrades.get('storage_size'),
                        'storage_space': upgrades.get('storage_space'),
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'Recorded company metrics for {stock_snapshot_date}'))

            # Check if the employees data exists
            if 'company_employees' in data and data['company_employees']:
                wage_count = 0
                total_employees = len(data['company_employees'])
                
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

                    # Always create a new Employee record every time the script runs
                    Employee.objects.create(
                        employee_id=employee_id,
                        company=company,
                        **employee_defaults
                    )

                    # Create or update DailyEmployeeSnapshot record
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
                    
                    # Get latest snapshot to preserve Switzerland travel tracking across days
                    existing_snapshot = DailyEmployeeSnapshot.objects.filter(
                        company=company,
                        employee_id=employee_id
                    ).order_by('-snapshot_date').first()
                    
                    # Track Switzerland travel status
                    status_desc = employee_data['status']['description']
                    
                    # Initialize Switzerland fields from existing snapshot or None
                    last_travelled_to_switzerland = existing_snapshot.last_travelled_to_switzerland if existing_snapshot else None
                    in_switzerland = existing_snapshot.in_switzerland if existing_snapshot else None
                    returning_from_switzerland = existing_snapshot.returning_from_switzerland if existing_snapshot else None
                    
                    # Update based on current status
                    if 'Traveling to Switzerland' in status_desc:
                        # Check if this is a NEW trip (previous trip was completed)
                        if returning_from_switzerland is not None:
                            # Previous trip completed, this is a new trip - reset all fields
                            last_travelled_to_switzerland = normalized_time
                            in_switzerland = None
                            returning_from_switzerland = None
                        elif not last_travelled_to_switzerland:
                            # First time traveling (no previous trip)
                            last_travelled_to_switzerland = normalized_time
                            in_switzerland = None
                            returning_from_switzerland = None
                        # else: keep existing timestamp (same ongoing trip)
                    elif 'In Switzerland' in status_desc:
                        # Employee has arrived in Switzerland
                        if not in_switzerland:
                            in_switzerland = normalized_time
                        # Keep last_travelled_to_switzerland, clear returning (still on current trip)
                        returning_from_switzerland = None
                    elif 'Returning from Switzerland' in status_desc:
                        # Employee is returning from Switzerland
                        if not returning_from_switzerland:
                            returning_from_switzerland = normalized_time
                        # Keep previous fields (still on same trip)
                    # If status doesn't mention Switzerland, preserve existing values
                    
                    # Add Switzerland fields to defaults
                    snapshot_defaults['last_travelled_to_switzerland'] = last_travelled_to_switzerland
                    snapshot_defaults['in_switzerland'] = in_switzerland
                    snapshot_defaults['returning_from_switzerland'] = returning_from_switzerland
                    
                    DailyEmployeeSnapshot.objects.update_or_create(
                        company=company,
                        employee_id=employee_id,
                        snapshot_date=snapshot_date,
                        defaults=snapshot_defaults
                    )

                    # Create or update CurrentEmployee record
                    CurrentEmployee.objects.update_or_create(
                        user_id=employee_id,
                        company_id=company_data['ID'],
                        defaults={
                            'username': employee_data['name'],
                            'company_name': company_data['name']
                        }
                    )
                
                # Delete CurrentEmployee records not in the current fetch (only after successful processing)
                current_employee_ids = set(int(eid) for eid in data['company_employees'].keys())
                deleted_count = CurrentEmployee.objects.filter(
                    company_id=company_data['ID']
                ).exclude(user_id__in=current_employee_ids).delete()[0]
                if deleted_count > 0:
                    self.stdout.write(f'Removed {deleted_count} outdated current employee records for company {company_data["ID"]}')
                
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