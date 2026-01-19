from django.shortcuts import render
from .models import Company, Employee, DailyEmployeeSnapshot, CurrentEmployee, Sale
import json
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Sum

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

    # Determine target company (default to 110380) and list companies with data in last 7 days
    last_week = timezone.now().date() - timedelta(days=7)
    available_companies = Company.objects.filter(
        dailyemployeesnapshot__snapshot_date__gte=last_week
    ).distinct().order_by('name')

    requested_company_id = request.GET.get('company_id')
    default_company_id = 110380
    if requested_company_id and requested_company_id.isdigit():
        target_company_id = int(requested_company_id)
    else:
        # Fall back to default if provided id missing/invalid
        target_company_id = default_company_id

    # If target company not in available list, fall back to first available or default
    if not available_companies.filter(company_id=target_company_id).exists():
        if available_companies.exists():
            target_company_id = available_companies.first().company_id
        else:
            target_company_id = default_company_id

    # Only include employees currently in the company (CurrentEmployee)
    current_member_ids = list(
        CurrentEmployee.objects.filter(company_id=target_company_id)
        .values_list('user_id', flat=True)
    )

    # Get all snapshots for target company with effectiveness_total > 0 and limited to current members
    all_snapshots = DailyEmployeeSnapshot.objects.filter(
        company__company_id=target_company_id,
        effectiveness_total__gt=0,
        employee_id__in=current_member_ids
    )

    # If no current members, short-circuit with empty data
    if not current_member_ids or not all_snapshots.exists():
        return render(request, 'company/employees.html', {
            'employees': [],
            'employee_data_json': mark_safe(json.dumps([], default=str)),
            'available_companies': available_companies,
            'selected_company_id': target_company_id
        })
    
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
    
    # Get historical data for all current members (not just currently-addicted ones)
    # This allows date range filtering to work across all members
    snapshots = all_snapshots.filter(
        employee_id__in=current_member_ids
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
        'employee_data_json': employee_data_json,
        'available_companies': available_companies,
        'selected_company_id': target_company_id
    })


def daily_sales_comparison(request):
    """
    Display daily sales metrics for both companies side-by-side (Polar Caps and Cornettow Caps)
    with both individual and combined values for each day
    """
    
    # Get all companies with sales data
    companies = Company.objects.filter(sale__isnull=False).distinct().order_by('name')
    
    if not companies.exists():
        return render(request, 'company/daily_sales_comparison.html', {
            'error': 'No sales data available',
            'companies': [],
            'sales_data': []
        })
    
    # Get date range from request
    days_back = request.GET.get('days', 30)
    try:
        days_back = int(days_back)
    except (ValueError, TypeError):
        days_back = 30
    
    start_date = timezone.now().date() - timedelta(days=days_back)
    
    # Get sales data for all companies
    sales = Sale.objects.filter(
        snapshot_date__gte=start_date
    ).order_by('-snapshot_date')
    
    # Group sales by date and organize by company
    sales_by_date = {}
    company_ids = set()
    
    for sale in sales:
        date_key = sale.snapshot_date
        company_ids.add(sale.company_id)
        
        if date_key not in sales_by_date:
            sales_by_date[date_key] = {}
        
        # Calculate derived metrics
        daily_income = sale.sold_worth or 0
        sold_amount = sale.sold_amount or 0
        created_amount = sale.created_amount or 0
        advertising_budget = sale.advertising_budget or 0
        
        # Calculate total wages for this company on this date from employee snapshots
        from django.db.models import Sum
        employee_wages = DailyEmployeeSnapshot.objects.filter(
            company=sale.company,
            snapshot_date=sale.snapshot_date
        ).aggregate(total_wages=Sum('wage'))['total_wages'] or 0
        
        # Calculate daily profit (revenue - wages - advertising)
        daily_profit = daily_income - employee_wages - advertising_budget
        
        # Calculate profit margin percentage
        profit_margin = ((daily_profit / daily_income) * 100) if daily_income > 0 else 0
        
        # Calculate value generated (using sold_worth as proxy)
        value_generated = daily_income
        
        sales_by_date[date_key][sale.company_id] = {
            'company_name': sale.company.name,
            'daily_income': daily_income,
            'price': sale.price or 0,
            'in_stock': sale.in_stock or 0,
            'sold_amount': sold_amount,
            'created_amount': created_amount,
            'popularity': sale.popularity or 0,
            'efficiency': sale.efficiency or 0,
            'environment': sale.environment or 0,
            'advertising_budget': sale.advertising_budget or 0,            'wages': employee_wages,            'daily_profit': daily_profit,
            'profit_margin': profit_margin,
            'value_generated': value_generated,
        }
    
    # Build combined data structure with both individual and totals
    combined_data = []
    
    for date_key in sorted(sales_by_date.keys(), reverse=True):
        date_entry = {
            'date': date_key,
            'companies': {},
            'totals': {
                'daily_income': 0,
                'sold_amount': 0,
                'created_amount': 0,
                'in_stock': 0,
                'advertising_budget': 0,
                'wages': 0,
                'daily_profit': 0,
                'value_generated': 0,
            }
        }
        
        # Add individual company data and calculate totals (sorted by company ID for consistent ordering)
        for company_id in sorted(sales_by_date[date_key].keys()):
            company_data = sales_by_date[date_key][company_id]
            date_entry['companies'][company_id] = company_data
            date_entry['totals']['daily_income'] += company_data['daily_income']
            date_entry['totals']['sold_amount'] += company_data['sold_amount']
            date_entry['totals']['created_amount'] += company_data['created_amount']
            date_entry['totals']['in_stock'] += company_data['in_stock']
            date_entry['totals']['advertising_budget'] += company_data['advertising_budget']
            date_entry['totals']['wages'] += company_data['wages']
            date_entry['totals']['daily_profit'] += company_data['daily_profit']
            date_entry['totals']['value_generated'] += company_data['value_generated']
        
        # Check if this is a Sunday (weekday() returns 6 for Sunday)
        is_sunday = date_key.weekday() == 6
        
        # If it's Sunday, calculate weekly summary for the past 7 days (this Sunday plus previous 6 days)
        if is_sunday:
            week_totals = {
                'daily_income': 0,
                'sold_amount': 0,
                'created_amount': 0,
                'in_stock': 0,
                'advertising_budget': 0,
                'wages': 0,
                'daily_profit': 0,
                'value_generated': 0,
            }
            
            # Sum up the current day and previous 6 days (Monday to Sunday)
            for day_offset in range(7):
                check_date = date_key - timedelta(days=day_offset)
                if check_date in sales_by_date:
                    for company_id in sales_by_date[check_date]:
                        day_data = sales_by_date[check_date][company_id]
                        week_totals['daily_income'] += day_data['daily_income']
                        week_totals['sold_amount'] += day_data['sold_amount']
                        week_totals['created_amount'] += day_data['created_amount']
                        week_totals['in_stock'] += day_data['in_stock']
                        week_totals['advertising_budget'] += day_data['advertising_budget']
                        week_totals['wages'] += day_data['wages']
                        week_totals['daily_profit'] += day_data['daily_profit']
                        week_totals['value_generated'] += day_data['value_generated']
            
            # Add weekly summary if we have data
            if any(v > 0 for v in week_totals.values()):
                week_start = date_key - timedelta(days=6)  # Monday
                week_end = date_key  # Sunday
                
                combined_data.append({
                    'is_weekly_summary': True,
                    'week_start': week_start,
                    'week_end': week_end,
                    'totals': week_totals
                })
        
        combined_data.append(date_entry)
    
    # Get all unique company IDs from database for complete list
    all_companies = list(companies)
    company_map = {c.company_id: c.name for c in all_companies}
    
    # Prepare JSON data for frontend
    data_json = mark_safe(json.dumps({
        'data': combined_data,
        'company_map': company_map,
        'days': days_back
    }, default=str))
    
    return render(request, 'company/daily_sales_comparison.html', {
        'companies': all_companies,
        'combined_data': combined_data,
        'company_map': company_map,
        'data_json': data_json,
        'days_back': days_back,
        'start_date': start_date,
        'end_date': timezone.now().date(),
    })