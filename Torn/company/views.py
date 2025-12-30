from django.shortcuts import render
from .models import Company, Employee, DailyEmployeeSnapshot
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
    # Get employee data from DailyEmployeeSnapshot model
    from django.db.models import Max
    from datetime import timedelta
    
    # Get all snapshots for company 110380 with effectiveness_total > 0
    all_snapshots = DailyEmployeeSnapshot.objects.filter(
        company__company_id=110380, 
        effectiveness_total__gt=0
    )
    
    # Find the most recent snapshot date
    most_recent_date = all_snapshots.aggregate(Max('snapshot_date'))['snapshot_date__max']
    
    # Get current member IDs and their latest snapshot records for alerts
    current_members = all_snapshots.filter(snapshot_date=most_recent_date)
    current_member_ids = list(current_members.values_list('employee_id', flat=True))
    
    # Get current addicted member IDs (addiction ≤ -6)
    current_addicted_member_ids = []
    for snapshot in current_members:
        if snapshot.effectiveness_addiction <= -6:
            current_addicted_member_ids.append(snapshot.employee_id)
    
    # Get historical data for members with current addiction issues
    snapshots = all_snapshots.filter(
        employee_id__in=current_addicted_member_ids
    ).order_by('snapshot_date')
    
    # Get Switzerland-related snapshot data for current addicted members
    switzerland_data = {}
    for emp_id in current_addicted_member_ids:
        # Get the latest Switzerland status info from the snapshot model fields
        latest_snapshot = all_snapshots.filter(
            employee_id=emp_id
        ).order_by('-snapshot_date').first()
        
        if latest_snapshot:
            switzerland_data[emp_id] = {
                'has_switzerland_status': latest_snapshot.in_switzerland is not None or 
                                         latest_snapshot.last_travelled_to_switzerland is not None,
                'to_switzerland': latest_snapshot.last_travelled_to_switzerland,
                'in_switzerland': latest_snapshot.in_switzerland,
                'from_switzerland': latest_snapshot.returning_from_switzerland
            }
        else:
            switzerland_data[emp_id] = {
                'has_switzerland_status': False,
                'to_switzerland': None,
                'in_switzerland': None,
                'from_switzerland': None
            }
    
    # Prepare data for chart from snapshots
    employee_data = list(snapshots.values(
        'employee_id', 'name', 'snapshot_date', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance', 'effectiveness_addiction', 'effectiveness_inactivity',
        'last_action_timestamp'))
    
    # Rename 'snapshot_date' to 'created_on' for compatibility with frontend
    for record in employee_data:
        record['created_on'] = record.pop('snapshot_date')
    
    # Add current member data for alerts (all current members, not just addicted ones)
    current_member_data = list(current_members.values(
        'employee_id', 'name', 'snapshot_date', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance', 'effectiveness_addiction', 'effectiveness_inactivity',
        'last_action_timestamp'))
    
    # Rename snapshot_date for current members
    for record in current_member_data:
        record['created_on'] = record.pop('snapshot_date')
    
    # Combine the datasets: historical data for charts + current data for alerts
    all_data_dict = {}
    
    # Add historical data for addicted members (for charts)
    for record in employee_data:
        key = f"{record['employee_id']}_{record['created_on']}"
        all_data_dict[key] = record
    
    # Add current member data (will overwrite if already exists)
    for record in current_member_data:
        key = f"{record['employee_id']}_{record['created_on']}"
        all_data_dict[key] = record
    
    # Convert back to list
    combined_employee_data = list(all_data_dict.values())
    
    # Add flags to identify current members and Switzerland data
    for record in combined_employee_data:
        record['is_current_member'] = record['created_on'] == most_recent_date
        
        # Add Switzerland data for current addicted members only
        if record['is_current_member'] and record['employee_id'] in current_addicted_member_ids and record['employee_id'] in switzerland_data:
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
        'employees': snapshots,
        'employee_data_json': employee_data_json
    })