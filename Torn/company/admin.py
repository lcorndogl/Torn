from django.contrib import admin
from .models import Company, Employee

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_id', 'name')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'company_name', 'position', 'effectiveness_working_stats','manual_labour', 'intelligence', 'endurance', 'created_on')
    list_filter = ('name', 'position')


    def company_name(self, obj):
        return obj.company.name
    company_name.admin_order_field = 'company'  # Allows column order sorting
    company_name.short_description = 'Company Name'  # Renames column head
