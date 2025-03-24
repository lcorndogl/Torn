from django.shortcuts import render
from .models import Company

def company_list(request):
    companies = Company.objects.all()
    return render(request, 'company_list.html', {'companies': companies})
