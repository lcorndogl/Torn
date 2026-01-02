from django.contrib import admin
from .models import Company, Employee, CurrentEmployee, DailyEmployeeSnapshot, Sale

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


@admin.register(DailyEmployeeSnapshot)
class DailyEmployeeSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        'snapshot_date', 'name', 'company_name', 'position',
        'formatted_wage', 'manual_labour', 'intelligence', 'endurance',
        'last_travelled_to_switzerland', 'in_switzerland', 'returning_from_switzerland'
    )
    list_filter = ('snapshot_date', 'company', 'position', 'status_description')
    search_fields = ('name', 'employee_id', 'company__name')
    readonly_fields = ('created_on', 'modified_on', 'last_travelled_to_switzerland', 
                       'in_switzerland', 'returning_from_switzerland')
    ordering = ['-snapshot_date', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('employee_id', 'name', 'company', 'position', 'snapshot_date')
        }),
        ('Financial', {
            'fields': ('wage',)
        }),
        ('Stats', {
            'fields': ('manual_labour', 'intelligence', 'endurance'),
            'classes': ('collapse',)
        }),
        ('Effectiveness', {
            'fields': (
                'effectiveness_working_stats', 'effectiveness_settled_in',
                'effectiveness_merits', 'effectiveness_director_education',
                'effectiveness_management', 'effectiveness_inactivity',
                'effectiveness_addiction', 'effectiveness_total'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Activity', {
            'fields': (
                'last_action_status', 'last_action_timestamp', 'last_action_relative',
                'status_description', 'status_state', 'status_until'
            ),
            'classes': ('collapse',)
        }),
        ('Travel Tracking - Switzerland', {
            'fields': ('last_travelled_to_switzerland', 'in_switzerland', 'returning_from_switzerland'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_on', 'modified_on'),
            'classes': ('collapse',)
        })
    )

    def company_name(self, obj):
        return obj.company.name
    company_name.admin_order_field = 'company'
    company_name.short_description = 'Company Name'

    def formatted_wage(self, obj):
        if obj.wage is not None:
            return f"${obj.wage:,}"
        return "Not available"
    formatted_wage.admin_order_field = 'wage'
    formatted_wage.short_description = 'Wage'


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('snapshot_date', 'company_name', 'product_name', 'formatted_price',
                    'formatted_created', 'formatted_sold', 'formatted_in_stock', 'formatted_sold_worth', 'efficiency', 'environment')
    list_filter = ('snapshot_date', 'company', 'product_name')
    search_fields = ('product_name', 'company__name')
    readonly_fields = ('created_on', 'modified_on')
    ordering = ['-snapshot_date', 'company']

    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'snapshot_date', 'product_name')
        }),
        ('Pricing & Inventory', {
            'fields': ('cost', 'rrp', 'price', 'in_stock', 'on_order'),
        }),
        ('Production & Sales', {
            'fields': ('created_amount', 'sold_amount', 'sold_worth'),
        }),
        ('Company Metrics', {
            'fields': ('popularity', 'efficiency', 'environment', 'advertising_budget', 'trains_available'),
        }),
        ('Upgrades', {
            'fields': ('company_size', 'staffroom_size', 'storage_size', 'storage_space'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_on', 'modified_on'),
            'classes': ('collapse',)
        })
    )

    def company_name(self, obj):
        return obj.company.name
    company_name.admin_order_field = 'company'
    company_name.short_description = 'Company Name'

    def formatted_price(self, obj):
        if obj.price is not None:
            return f"${obj.price:,}"
        return "-"
    formatted_price.admin_order_field = 'price'
    formatted_price.short_description = 'Price'

    def formatted_created(self, obj):
        if obj.created_amount is not None:
            return f"{obj.created_amount:,}"
        return "-"
    formatted_created.admin_order_field = 'created_amount'
    formatted_created.short_description = 'Created'

    def formatted_sold(self, obj):
        if obj.sold_amount is not None:
            return f"{obj.sold_amount:,}"
        return "-"
    formatted_sold.admin_order_field = 'sold_amount'
    formatted_sold.short_description = 'Sold'

    def formatted_in_stock(self, obj):
        if obj.in_stock is not None:
            return f"{obj.in_stock:,}"
        return "-"
    formatted_in_stock.admin_order_field = 'in_stock'
    formatted_in_stock.short_description = 'In Stock'

    def formatted_sold_worth(self, obj):
        if obj.sold_worth is not None:
            return f"${obj.sold_worth:,}"
        return "-"
    formatted_sold_worth.admin_order_field = 'sold_worth'
    formatted_sold_worth.short_description = 'Sold Worth'


