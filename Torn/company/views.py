from django.shortcuts import render
from .models import Company, Employee
import json
from django.utils.safestring import mark_safe

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
    # Filter employees to only show those from company ID 110380, exclude total effectiveness of 0, ordered by created_on
    employees = Employee.objects.filter(company__company_id=110380, effectiveness_total__gt=0).order_by('created_on')
    
    # Get the most recent created_on date to identify current members
    from django.db.models import Max
    most_recent_date = employees.aggregate(Max('created_on'))['created_on__max']
    
    # Prepare data for chart: include ALL historical data for charts
    employee_data = list(employees.values(
        'employee_id', 'name', 'created_on', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance', 'effectiveness_addiction', 'effectiveness_inactivity',
        'last_action_timestamp'))
    
    # Add a flag to identify current members (most recent date records)
    for record in employee_data:
        record['is_current_member'] = record['created_on'] == most_recent_date
    
    employee_data_json = mark_safe(json.dumps(employee_data, default=str))
    return render(request, 'company/employees.html', {
        'employees': employees,
        'employee_data_json': employee_data_json
    })