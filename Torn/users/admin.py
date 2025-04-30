from django.contrib import admin
from .models import UserList, UserRecord, UserOrganisedCrimeCPR
from import_export.admin import ImportExportModelAdmin

class UserListAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'game_name')

class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'level', 'current_faction', 'days_in_faction', 'created_on')
    list_filter = ('current_faction', 'user_id')

class UserOrganisedCrimeCPRAdmin(admin.ModelAdmin):
    list_display = ('user', 'organised_crime_role', 'user_cpr')
    list_filter = ('organised_crime_role',)

admin.site.register(UserList, UserListAdmin)
admin.site.register(UserRecord, UserRecordAdmin)
admin.site.register(UserOrganisedCrimeCPR, UserOrganisedCrimeCPRAdmin)  # Register the new model
# Register your models here.
