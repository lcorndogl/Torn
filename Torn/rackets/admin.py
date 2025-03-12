from django.contrib import admin
from .models import Rackets

@admin.register(Rackets)
class RacketsAdmin(admin.ModelAdmin):
    list_display = ('territory', 'name', 'level', 'reward', 'created', 'changed', 'faction', 'timestamp')
    search_fields = ('territory', 'name', 'faction')
    list_filter = ('level', 'faction')

# Alternatively, you can use the following simpler registration:
# admin.site.register(Rackets)
