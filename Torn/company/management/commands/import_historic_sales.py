import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from company.models import Company, Sale


class Command(BaseCommand):
    help = 'Import historic sales data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file to import'
        )
        parser.add_argument(
            '--company-id',
            type=int,
            default=110380,
            help='Company ID to associate with the data (default: 110380)'
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        company_id = kwargs['company_id']

        # Get or create the company
        company, created = Company.objects.get_or_create(
            company_id=company_id,
            defaults={'name': 'Polar Caps'}  # Default name
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created company: {company.name}'))
        else:
            self.stdout.write(f'Using existing company: {company.name}')

        imported_count = 0
        skipped_count = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Read all lines first to handle the header correctly
                lines = f.readlines()
                
                # Find the header row (starts with "Date,")
                header_idx = None
                for idx, line in enumerate(lines):
                    if line.startswith('Date,'):
                        header_idx = idx
                        break
                
                if header_idx is None:
                    self.stdout.write(self.style.ERROR('Could not find header row starting with "Date,"'))
                    return

                # Parse from header onwards
                reader = csv.DictReader(lines[header_idx:])
                
                for row_num, row in enumerate(reader, start=header_idx + 1):
                    # Skip week summary rows and empty rows
                    date_val = row.get('Date', '').strip()
                    if not date_val or 'Week' in date_val:
                        skipped_count += 1
                        continue

                    try:
                        # Parse the date
                        snapshot_date = datetime.strptime(date_val, '%d/%m/%Y').date()

                        # Parse numeric fields, removing commas
                        def parse_int(value):
                            if not value or value.strip() == '':
                                return None
                            return int(str(value).replace(',', '').replace('£', ''))

                        # Extract data
                        daily_income = parse_int(row.get('daily_income'))
                        advertising_budget = parse_int(row.get('ad_budget'))
                        price = parse_int(row.get('barrel price'))
                        in_stock = parse_int(row.get('in_stock'))
                        sold_amount = parse_int(row.get('sold_amount'))
                        created_amount = parse_int(row.get('produced_today'))
                        popularity = parse_int(row.get('Popularity'))
                        efficiency = parse_int(row.get('Efficiency'))
                        environment = parse_int(row.get('Environment'))

                        # Create or update the Sale record
                        sale, created_sale = Sale.objects.update_or_create(
                            company=company,
                            snapshot_date=snapshot_date,
                            defaults={
                                'product_name': 'Oil (Barrel)',
                                'price': price,
                                'in_stock': in_stock,
                                'sold_amount': sold_amount,
                                'created_amount': created_amount,
                                'popularity': popularity,
                                'efficiency': efficiency,
                                'environment': environment,
                                'advertising_budget': advertising_budget,
                            }
                        )

                        if created_sale:
                            imported_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(
                                f'Updated existing record for {snapshot_date}'
                            ))

                    except (ValueError, KeyError) as e:
                        self.stdout.write(self.style.WARNING(
                            f'Error parsing row {row_num}: {str(e)} | {date_val}'
                        ))
                        skipped_count += 1
                        continue

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Import complete! Imported: {imported_count}, Skipped: {skipped_count}'
        ))
