from django.shortcuts import render
from .models import Company, Employee
import json
from django.utils.safestring import mark_safe

def company_list(request):
    companies = Company.objects.all()
    return render(request, 'company/company_list.html', {'companies': companies})

def eternal_workstats(request):
    employees = Employee.objects.all()
    # Prepare data for chart: include manual_labour, intelligence, endurance
    employee_data = list(employees.values(
        'employee_id', 'name', 'created_on', 'effectiveness_working_stats',
        'manual_labour', 'intelligence', 'endurance'))
    employee_data_json = mark_safe(json.dumps(employee_data, default=str))
    return render(request, 'company/eternal_workstats.html', {
        'employees': employees,
        'employee_data_json': employee_data_json
    })