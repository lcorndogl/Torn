from django.contrib import admin
from .models import UserList, UserRecord

class UserListAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'game_name')

class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'level', 'days_in_faction', 'created_on')

admin.site.register(UserList, UserListAdmin)
admin.site.register(UserRecord, UserRecordAdmin)

# Register your models here.
