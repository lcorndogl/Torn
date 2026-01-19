from django.urls import path
from . import views

urlpatterns = [
    path('eg', views.eternal_workstats, name='eternal_workstats'),
    path('pc', views.employees, name='employees'),
    path('sales', views.daily_sales_comparison, name='daily_sales_comparison'),
    path('', views.company_list, name='company_list'),
]
