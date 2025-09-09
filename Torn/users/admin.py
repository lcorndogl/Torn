from django.contrib import admin
from .models import (
    UserList,
    UserRecord,
    UserOrganisedCrimeCPR,
    TornUserProfile
)

class UserListAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'game_name')

class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'level', 'current_faction', 'days_in_faction', 'created_on')
    list_filter = ('current_faction', 'user_id')

class UserOrganisedCrimeCPRAdmin(admin.ModelAdmin):
    list_display = ('user', 'organised_crime_role', 'user_cpr')
    list_filter = ('organised_crime_role',)


class TornUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tornuser', 'tornapi', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'tornuser', 'tornapi')
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(UserList, UserListAdmin)
admin.site.register(UserRecord, UserRecordAdmin)
admin.site.register(UserOrganisedCrimeCPR, UserOrganisedCrimeCPRAdmin)
admin.site.register(TornUserProfile, TornUserProfileAdmin)
# Register your models here.
