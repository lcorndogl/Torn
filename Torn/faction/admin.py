from django.contrib import admin
from .models import Faction

@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ('faction_id', 'name', 'tag', 'respect')
    search_fields = ('name', 'tag')
    list_filter = ('respect',)
