from django.contrib import admin
from .models import Racket, Territory  # Import Territory model

@admin.register(Racket)
class RacketAdmin(admin.ModelAdmin):
    list_display = ('territory', 'name', 'level', 'reward', 'created', 'changed', 'faction', 'timestamp')
    search_fields = ('territory', 'name', 'faction')
    list_filter = ('level', 'faction')

@admin.register(Territory)  # Register Territory model
class TerritoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
