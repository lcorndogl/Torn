from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.modify_profile, name='modify_profile'),
    path('profile/toggle/<int:profile_id>/', 
         views.toggle_active, 
         name='toggle_active'),
    path('profile/delete/<int:profile_id>/', 
         views.delete_profile, 
         name='delete_profile'),
    path('profile/add/', views.addApiKey, name='addApiKey'),
]
