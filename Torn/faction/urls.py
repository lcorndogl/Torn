from django.urls import path
from . import views

urlpatterns = [
    path('faction-comparison/', views.faction_comparison, name='faction_comparison'),
]