from django.contrib import admin
from .models import Company, Employee, CurrentEmployee

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_id', 'name')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'company_name', 'position', 'formatted_wage', 'effectiveness_working_stats','manual_labour', 'intelligence', 'endurance', 'status_description','created_on')
    list_filter = ('position', 'status_description', 'company')
    search_fields = ('name', 'position', 'employee_id')
    readonly_fields = ('employee_id', 'created_on')
    ordering = ('-created_on', '-wage', 'name')  # Order by newest fetch first, then highest wage, then name
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('employee_id', 'name', 'company', 'position')
        }),
        ('Financial', {
            'fields': ('wage',)
        }),
        ('Stats', {
            'fields': ('manual_labour', 'intelligence', 'endurance'),
            'classes': ('collapse',)  # Make this section collapsible
        }),
        ('Effectiveness', {
            'fields': (
                'effectiveness_working_stats', 'effectiveness_settled_in', 
                'effectiveness_merits', 'effectiveness_director_education',
                'effectiveness_management', 'effectiveness_inactivity',
                'effectiveness_addiction', 'effectiveness_total'
            ),
            'classes': ('collapse',)  # Make this section collapsible
        }),
        ('Status & Activity', {
            'fields': (
                'last_action_status', 'last_action_timestamp', 'last_action_relative',
                'status_description', 'status_state', 'status_until'
            ),
            'classes': ('collapse',)  # Make this section collapsible
        }),
        ('Metadata', {
            'fields': ('created_on',),
            'classes': ('collapse',)
        })
    )


    def company_name(self, obj):
        return obj.company.name
    company_name.admin_order_field = 'company'  # Allows column order sorting
    company_name.short_description = 'Company Name'  # Renames column head

    def formatted_wage(self, obj):
        if obj.wage is not None:
            return f"${obj.wage:,}"
        return "Not available"
    formatted_wage.admin_order_field = 'wage'  # Allows column order sorting
    formatted_wage.short_description = 'Wage'  # Renames column head


@admin.register(CurrentEmployee)
class CurrentEmployeeAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'company_id', 'company_name', 'created_on', 'updated_on')
    list_filter = ('company_name',)
    search_fields = ('username', 'user_id', 'company_name')
    readonly_fields = ('created_on', 'updated_on')
    ordering = ('-updated_on',)
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('user_id', 'username')
        }),
        ('Company Information', {
            'fields': ('company_id', 'company_name')
        }),
        ('Metadata', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        })
    )
