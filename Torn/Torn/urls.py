"""
URL configuration for Torn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('territories/', include('racket.urls')),  # Include the racket app's URLs
    path('rackets/', include('racket.urls')),  # Include the racket app's URLs
    path('company/', include('company.urls')),  # Include the company app's URLs
    path('faction/', include('faction.urls')),  # Include the faction app's URLs
    # path('', admin.site.urls),  # Redirect root URL to admin site

]
