from django.urls import path
from . import views

urlpatterns = [
    path('eg', views.eternal_workstats, name='eternal_workstats'),
    path('', views.company_list, name='company_list'),
]
