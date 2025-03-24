import requests
from django.core.management.base import BaseCommand
from company.models import Company, Employee
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetch company data from the Torn API and insert it into the database'

    def handle(self, *args, **kwargs):
        url = 'https://api.torn.com/company/104351?selections=profile,employees&key=bk8mXQgk2EvJyzrz'
        response = requests.get(url)
        data = response.json()

        # Check if the company data exists
        if 'company' in data:
            company_data = data['company']
            company, created = Company.objects.get_or_create(
                company_id=company_data['ID'],
                defaults={'name': company_data['name']}
            )

        # Check if the employees data exists
        if 'company_employees' in data:
            for employee_id, employee_data in data['company_employees'].items():
                status_until = employee_data['status']['until']
                if status_until == 0:
                    status_until = None
                else:
                    status_until = datetime.fromtimestamp(status_until)

                Employee.objects.create(
                    employee_id=employee_id,
                    company=company,
                    name=employee_data['name'],
                    position=employee_data['position'],
                    manual_labour=employee_data['manual_labor'],
                    intelligence=employee_data['intelligence'],
                    endurance=employee_data['endurance'],
                    effectiveness_working_stats=employee_data['effectiveness'].get('working_stats', 0),
                    effectiveness_settled_in=employee_data['effectiveness'].get('settled_in', 0),
                    effectiveness_merits=employee_data['effectiveness'].get('merits', 0),
                    effectiveness_director_education=employee_data['effectiveness'].get('director_education', 0),
                    effectiveness_management=employee_data['effectiveness'].get('management', 0),
                    effectiveness_inactivity=employee_data['effectiveness'].get('inactivity', 0),
                    effectiveness_addiction=employee_data['effectiveness'].get('addiction', 0),
                    effectiveness_total=employee_data['effectiveness'].get('total', 0),
                    last_action_status=employee_data['last_action']['status'],
                    last_action_timestamp=datetime.fromtimestamp(employee_data['last_action']['timestamp']),
                    last_action_relative=employee_data['last_action']['relative'],
                    status_description=employee_data['status']['description'],
                    status_state=employee_data['status']['state'],
                    status_until=status_until,
                    created_on=datetime.now()
                )
        else:
            self.stdout.write(self.style.WARNING('No employees data found in the response'))

        self.stdout.write(self.style.SUCCESS('Successfully fetched and inserted company data'))