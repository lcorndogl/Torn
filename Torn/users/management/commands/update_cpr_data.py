import requests
from html.parser import HTMLParser
from django.core.management.base import BaseCommand
from users.models import UserList, UserOrganisedCrimeCPR
from faction.models import OrganisedCrimeRole


class Command(BaseCommand):
    help = "Update CPR data from a published Google Spreadsheet"

    def handle(self, *args, **kwargs):
        # URL of the published Google Spreadsheet in HTML format
        html_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSCHZiuE4VN-eXhUOV_q-ojuJK0mUN70pXIxqfIcxNBvup7sGi_H2HO02f_5TrYwln2rERp5rSVSP-M/pubhtml"

        # Fetch the HTML content
        response = requests.get(html_url)
        response.raise_for_status()  # Raise an error if the request failed
        html_content = response.text

        # Custom HTML parser to extract table data
        class TableParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_table = False
                self.in_row = False
                self.in_cell = False
                self.current_row = []
                self.table_data = []
                self.cell_colspan = 1  # Tracks the colspan of the current cell

            def handle_starttag(self, tag, attrs):
                if tag == "table":
                    self.in_table = True
                elif tag == "tr" and self.in_table:
                    self.in_row = True
                    self.current_row = []
                elif tag == "td" and self.in_row:
                    self.in_cell = True
                    # Check for colspan attribute
                    self.cell_colspan = 1  # Default colspan is 1
                    for attr_name, attr_value in attrs:
                        if attr_name == "colspan":
                            self.cell_colspan = int(attr_value)

            def handle_endtag(self, tag):
                if tag == "table":
                    self.in_table = False
                elif tag == "tr" and self.in_row:
                    self.in_row = False
                    self.table_data.append(self.current_row)
                elif tag == "td" and self.in_cell:
                    self.in_cell = False

            def handle_data(self, data):
                if self.in_cell:
                    # Add the cell data, repeated for the colspan
                    for _ in range(self.cell_colspan):
                        self.current_row.append(data.strip())

        # Parse the HTML content
        parser = TableParser()
        parser.feed(html_content)

        # Extract the table data
        table_data = parser.table_data

        # Debugging: Print the entire table data
        self.stdout.write(f"Table Data: {table_data}")

        # Ensure there are at least 3 rows (header, roles, and data)
        if len(table_data) < 3:
            self.stdout.write(self.style.ERROR("Spreadsheet does not have enough rows to process."))
            return

        # Preprocess Row 1 to handle merged cells (fill forward)
        def preprocess_merged_cells(row):
            filled_row = []
            current_value = None
            for cell in row:
                if cell:  # If the cell is not empty, update the current value
                    current_value = cell
                filled_row.append(current_value)  # Fill forward the current value
            return filled_row

        # Preprocess the roles row (Row 1)
        table_data[1] = preprocess_merged_cells(table_data[1])

        # Debugging: Print the preprocessed roles row
        self.stdout.write(f"Preprocessed Roles Row: {table_data[1]}")

        # Row 1: Organised Crime Role and Level (e.g., "Break The Bank (5)")
        roles_row = table_data[0]

        # Row 3: Role names (e.g., "Muscle", "Robber")
        role_names_row = table_data[2]

        # Debugging: Print roles_row and role_names_row
        self.stdout.write(f"Roles Row: {roles_row}")
        self.stdout.write(f"Role Names Row: {role_names_row}")

        # Process each member (starting from row 6, as rows 1-5 are headers/metadata)
        for member_row in table_data[5:]:  # Start from row 6 (index 5)
            if len(member_row) < 1:
                continue  # Skip empty rows

            # Column A: game_name
            game_name = member_row[0].strip()

            # Skip rows with invalid or non-user data
            if game_name in ['Member', 'Completed', 'Left to Go', 'Meet Requirements']:
                self.stdout.write(self.style.WARNING(f"Skipping non-user row with game_name '{game_name}'."))
                continue

            # Print the raw data for the current row
            self.stdout.write(f"Raw Row Data: {member_row}")

            try:
                user = UserList.objects.get(game_name=game_name)
            except UserList.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User with game_name '{game_name}' not found. Skipping."))
                continue

            # Process each column (starting from column B)
            for col_index, user_cpr_value in enumerate(member_row[1:], start=1):
                # Skip if the column index exceeds the number of columns in the roles row
                if col_index >= len(table_data[1]) or col_index >= len(table_data[3]):
                    continue

                # Fetch the organised crime role and CPR as a tuple
                try:
                    organised_crime_role_level = table_data[1][col_index]  # Row 2, same column
                    role_name = table_data[3][col_index]  # Row 4, same column
                    user_cpr = int(user_cpr_value)  # Validate CPR value
                except (IndexError, ValueError):
                    self.stdout.write(self.style.WARNING(f"Skipping invalid data at column {col_index} for user '{game_name}'."))
                    continue

                # Extract crime_name and level from organised_crime_role_level
                crime_name = organised_crime_role_level.split('(')[0].strip()
                level = int(organised_crime_role_level.split('(')[1].strip(')'))

                # Find the OrganisedCrimeRole object based on crime_name and role
                try:
                    organised_crime_role = OrganisedCrimeRole.objects.get(crime_name=crime_name, role=role_name)
                except OrganisedCrimeRole.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"OrganisedCrimeRole not found for crime_name='{crime_name}' and role='{role_name}'. Skipping."))
                    continue

                # Print the processed data for the current cell
                self.stdout.write(f"Processed Data: User='{game_name}', Role='{organised_crime_role.id}', CPR='{user_cpr}'")

                # Check if a record already exists for this user and role
                try:
                    existing_record = UserOrganisedCrimeCPR.objects.get(user=user, organised_crime_role=organised_crime_role)
                    if user_cpr > existing_record.user_cpr:  # Update only if the new value is higher
                        existing_record.user_cpr = user_cpr
                        existing_record.save()
                        self.stdout.write(self.style.SUCCESS(f"Updated CPR for user '{game_name}' and role '{organised_crime_role.id}' to {user_cpr}."))
                    else:
                        self.stdout.write(self.style.WARNING(f"Existing CPR for user '{game_name}' and role '{organised_crime_role.id}' is higher or equal. Skipping."))
                except UserOrganisedCrimeCPR.DoesNotExist:
                    # Create a new record if it doesn't exist
                    UserOrganisedCrimeCPR.objects.create(
                        user=user,
                        organised_crime_role=organised_crime_role,
                        user_cpr=user_cpr
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created new CPR record for user '{game_name}' and role '{organised_crime_role.id}' with value {user_cpr}."))