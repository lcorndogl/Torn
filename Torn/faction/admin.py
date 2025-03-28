from django.contrib import admin
from .models import Faction, FactionList

@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    list_display = ('faction_id', 'faction_name', 'faction_tag', 'respect')
    search_fields = ('faction_id__name', 'faction_id__tag')
    list_filter = ('respect',)

    def faction_name(self, obj):
        return obj.faction_id.name
    faction_name.admin_order_field = 'faction_id__name'
    faction_name.short_description = 'Faction Name'

    def faction_tag(self, obj):
        return obj.faction_id.tag
    faction_tag.admin_order_field = 'faction_id__tag'
    faction_tag.short_description = 'Faction Tag'

@admin.register(FactionList)
class FactionListAdmin(admin.ModelAdmin):
    list_display = ('faction_id', 'name', 'tag')
    search_fields = ('name', 'tag')
