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
    # Get date range from request parameters, default to last 30 days
    from django.db.models import Max, Min
    from datetime import timedelta
    
    # Get date range parameters from URL or use defaults
    end_date_str = request.GET.get('end_date')
    start_date_str = request.GET.get('start_date')
    
    # Set default date range to last 7 days (since most data is recent)
    now = timezone.now()
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            # Set to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            end_date = now
    else:
        end_date = now
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            # Set to start of day
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            start_date = now - timedelta(days=7)
    else:
        start_date = now - timedelta(days=7)
    
    # Filter employees to only show those from company ID 110380, exclude total effectiveness of 0, 
    # and limit to the specified date range
    employees = Employee.objects.filter(
        company__company_id=110380, 
        effectiveness_total__gt=0,
        created_on__gte=start_date,
        created_on__lte=end_date
    ).order_by('created_on')
    
    # Get the most recent created_on date to identify current members
    # We need to check the actual most recent date from all data, not just filtered data
    all_employees = Employee.objects.filter(company__company_id=110380, effectiveness_total__gt=0)
    most_recent_date = all_employees.aggregate(Max('created_on'))['created_on__max']
    
    # Calculate Switzerland status data for the last 24 hours
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    # Get current member IDs (from the most recent date, not filtered date range)
    current_member_ids = all_employees.filter(created_on=most_recent_date).values_list('employee_id', flat=True).distinct()
    
    # First, identify who has current addictions (≤ -6)
    addicted_member_ids = []
    for emp_id in current_member_ids:
        latest_record = all_employees.filter(employee_id=emp_id, created_on=most_recent_date).first()
        if latest_record and latest_record.effectiveness_addiction <= -6:
            addicted_member_ids.append(emp_id)
    
    # Only get Switzerland data for addicted members
    switzerland_data = {}
    for emp_id in addicted_member_ids:
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
    
    # Prepare data for chart: include ALL historical data for charts plus Switzerland info
    employee_data = list(employees.values(
        'employee_id', 'name', 'created_on', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance', 'effectiveness_addiction', 'effectiveness_inactivity',
        'last_action_timestamp'))
    
    # Add a flag to identify current members and Switzerland data
    for record in employee_data:
        record['is_current_member'] = record['created_on'] == most_recent_date
        
        # Add Switzerland data for current members
        if record['is_current_member'] and record['employee_id'] in switzerland_data:
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
    
    employee_data_json = mark_safe(json.dumps(employee_data, default=str))
    
    # Format dates for template
    start_date_formatted = start_date.strftime('%Y-%m-%d')
    end_date_formatted = end_date.strftime('%Y-%m-%d')
    
    return render(request, 'company/employees.html', {
        'employees': employees,
        'employee_data_json': employee_data_json,
        'start_date': start_date_formatted,
        'end_date': end_date_formatted,
        'total_records': employees.count()
    })