from django.contrib import admin
from .models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'created_on')

admin.site.register(User, UserAdmin)

# Register your models here.
