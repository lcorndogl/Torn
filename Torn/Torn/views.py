from django.shortcuts import render


def home(request):
    """
    Homepage view
    """
    return render(request, 'home.html')


def api(request):
    """
    API view
    """
    return render(request, 'api_use.html')
