from django.shortcuts import render
from .models import Company, Employee
import json
from django.utils.safestring import mark_safe
from datetime import datetime
from django.utils import timezone

def company_list(request):
    companies = Company.objects.all()
    return render(request, 'company/company_list.html', {'companies': companies})

def eternal_workstats(request):
    # Filter employees to only show those from company ID 104351, exclude total effectiveness of 0, ordered by created_on
    employees = Employee.objects.filter(company__company_id=104351, effectiveness_total__gt=0).order_by('created_on')
    # Prepare data for chart: include manual_labour, intelligence, endurance, and addiction
    employee_data = list(employees.values(
        'employee_id', 'name', 'created_on', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance', 'effectiveness_addiction'))
    employee_data_json = mark_safe(json.dumps(employee_data, default=str))
    return render(request, 'company/eternal_workstats.html', {
        'employees': employees,
        'employee_data_json': employee_data_json
    })

def employees(request):
    # First, get current members and identify who has current addictions (≤ -6)
    from django.db.models import Max, Min
    from django.utils import timezone
    from datetime import timedelta
    
    # Get all employees to find current members first
    all_employees = Employee.objects.filter(company__company_id=110380, effectiveness_total__gt=0)
    most_recent_date = all_employees.aggregate(Max('created_on'))['created_on__max']
    
    # Get current member IDs and their latest records for alerts
    current_members = all_employees.filter(created_on=most_recent_date)
    current_member_ids = list(current_members.values_list('employee_id', flat=True))
    
    # Get current addicted member IDs for historical chart data
    current_addicted_member_ids = []
    for record in current_members:
        if record.effectiveness_addiction <= -6:
            current_addicted_member_ids.append(record.employee_id)
    
    # For charts: Only pull historical data for members with current addiction issues
    # For alerts: We'll add current member data separately
    employees = Employee.objects.filter(
        company__company_id=110380, 
        effectiveness_total__gt=0,
        employee_id__in=current_addicted_member_ids
    ).order_by('created_on')
    
    # Calculate Switzerland status data for the last 24 hours
    now = timezone.now()
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    # Get Switzerland status data for current addicted members only
    addicted_member_ids = current_addicted_member_ids
    
    # Only get Switzerland data for addicted members (which is all current members in our filtered dataset)
    switzerland_data = {}
    for emp_id in current_addicted_member_ids:
        # Get Switzerland-related statuses for this employee in the last 24 hours
        switzerland_records = Employee.objects.filter(
            employee_id=emp_id,
            status_description__icontains='switzerland',
            created_on__gte=twenty_four_hours_ago
        ).values('created_on', 'status_description').order_by('-created_on')
        
        if switzerland_records.exists():
            # Find the last occurrence of each status type
            to_switzerland = None
            in_switzerland = None
            from_switzerland = None
            
            # Convert to list and sort chronologically (oldest first) for easier chain analysis
            switzerland_list = list(switzerland_records.order_by('created_on'))
            
            # Find the current active chain by working backwards from the most recent status
            # to find where the current chain started
            chain_start_index = 0
            
            # Look for the most recent 'from switzerland' that would end a previous chain
            for i in range(len(switzerland_list) - 1, -1, -1):
                status = switzerland_list[i]['status_description'].lower()
                if 'from switzerland' in status:
                    # This ends a chain, so current chain starts after this
                    chain_start_index = i + 1
                    break
            
            # Now find the first 'to switzerland' in the current chain (starting from chain_start_index)
            for i in range(chain_start_index, len(switzerland_list)):
                status = switzerland_list[i]['status_description'].lower()
                if 'to switzerland' in status:
                    to_switzerland = switzerland_list[i]['created_on']
                    break
            
            # Second pass: find the earliest and latest 'in switzerland' that's after the found 'to switzerland'
            if to_switzerland:
                in_switzerland_earliest = None
                in_switzerland_latest = None
                
                for record in switzerland_list:  # Already in chronological order
                    status = record['status_description'].lower()
                    if 'in switzerland' in status and record['created_on'] > to_switzerland:
                        if in_switzerland_earliest is None:
                            in_switzerland_earliest = record['created_on']
                        in_switzerland_latest = record['created_on']  # Keep updating to get the latest
                
                # Store as a tuple if we found any records
                if in_switzerland_earliest:
                    in_switzerland = (in_switzerland_earliest, in_switzerland_latest)
            else:
                # If no 'to switzerland' found, just get the most recent 'in switzerland'
                for i in range(len(switzerland_list) - 1, -1, -1):
                    status = switzerland_list[i]['status_description'].lower()
                    if 'in switzerland' in status:
                        in_switzerland = switzerland_list[i]['created_on']
                        break
            
            # Third pass: find the earliest 'from switzerland' that's after the found 'to switzerland'
            if to_switzerland:
                for record in switzerland_list:  # Already in chronological order
                    status = record['status_description'].lower()
                    if 'from switzerland' in status and record['created_on'] > to_switzerland:
                        from_switzerland = record['created_on']
                        break
            else:
                # If no 'to switzerland' found, just get the most recent 'from switzerland'
                for i in range(len(switzerland_list) - 1, -1, -1):
                    status = switzerland_list[i]['status_description'].lower()
                    if 'from switzerland' in status:
                        from_switzerland = switzerland_list[i]['created_on']
                        break
            
            switzerland_data[emp_id] = {
                'has_switzerland_status': True,
                'to_switzerland': to_switzerland,
                'in_switzerland': in_switzerland,
                'from_switzerland': from_switzerland
            }
        else:
            switzerland_data[emp_id] = {
                'has_switzerland_status': False,
                'to_switzerland': None,
                'in_switzerland': None,
                'from_switzerland': None
            }
    
    # Prepare data for chart: include historical data for addicted members only
    employee_data = list(employees.values(
        'employee_id', 'name', 'created_on', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance', 'effectiveness_addiction', 'effectiveness_inactivity',
        'last_action_timestamp'))
    
    # Add current member data for alerts (all current members, not just addicted ones)
    current_member_data = list(current_members.values(
        'employee_id', 'name', 'created_on', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance', 'effectiveness_addiction', 'effectiveness_inactivity',
        'last_action_timestamp'))
    
    # Combine the datasets: historical data for charts + current data for alerts
    # Remove duplicates by using a dict with employee_id+date as key
    all_data_dict = {}
    
    # Add historical data for addicted members (for charts)
    for record in employee_data:
        key = f"{record['employee_id']}_{record['created_on']}"
        all_data_dict[key] = record
    
    # Add current member data (will overwrite if already exists, which is fine)
    for record in current_member_data:
        key = f"{record['employee_id']}_{record['created_on']}"
        all_data_dict[key] = record
    
    # Convert back to list
    combined_employee_data = list(all_data_dict.values())
    
    # Add flags to identify current members and Switzerland data
    for record in combined_employee_data:
        record['is_current_member'] = record['created_on'] == most_recent_date
        
        # Add Switzerland data for current addicted members only
        if record['is_current_member'] and record['employee_id'] in addicted_member_ids and record['employee_id'] in switzerland_data:
            sw_data = switzerland_data[record['employee_id']]
            record['switzerland_status'] = sw_data['has_switzerland_status']
            record['switzerland_to'] = sw_data['to_switzerland']
            record['switzerland_in'] = sw_data['in_switzerland']
            record['switzerland_from'] = sw_data['from_switzerland']
        else:
            record['switzerland_status'] = False
            record['switzerland_to'] = None
            record['switzerland_in'] = None
            record['switzerland_from'] = None
    
    employee_data_json = mark_safe(json.dumps(combined_employee_data, default=str))
    return render(request, 'company/employees.html', {
        'employees': employees,
        'employee_data_json': employee_data_json
    })