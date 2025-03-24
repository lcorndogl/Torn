from django.urls import path
from . import views

urlpatterns = [
    # path('rackets/', views.rackets_list, name='rackets_list'),
    # path('', views.rackets_list, name='rackets_list')
    path('', views.companies_list, name='companies_list')
]
