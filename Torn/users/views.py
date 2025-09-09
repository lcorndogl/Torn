from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TornUserProfile
import requests
import json


def fetch_torn_username(api_key):
    """
    Fetch username from Torn API using the provided API key.
    Returns tuple (username, success_bool, error_message)
    """
    try:
        url = 'https://api.torn.com/v2/user/basic'
        headers = {
            'accept': 'application/json',
            'Authorization': f'ApiKey {api_key}'
        }
        params = {'striptags': 'true'}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Check for error in response first
            if 'error' in data:
                error_msg = data['error'].get('error', 'Unknown API error')
                if data['error'].get('code') == 2:
                    return None, False, "Invalid API key"
                else:
                    return None, False, f"API error: {error_msg}"
            elif 'profile' in data and 'name' in data['profile']:
                return data['profile']['name'], True, None
            else:
                return None, False, "Invalid API response format"
        elif response.status_code == 403:
            return None, False, "Invalid API key"
        else:
            return None, False, f"API request failed with status {response.status_code}"
            
    except requests.RequestException as e:
        return None, False, f"Network error: {str(e)}"
    except json.JSONDecodeError:
        return None, False, "Invalid JSON response from API"
    except Exception as e:
        return None, False, f"Unexpected error: {str(e)}"


@login_required
def modify_profile(request):
    """
    View to display and handle the modify profile page.
    """
    user_profiles = TornUserProfile.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    context = {
        'user': request.user,
        'user_profiles': user_profiles,
    }
    
    return render(request, 'users/modify_profile.html', context)


@login_required
def toggle_active(request, profile_id):
    """
    Toggle the is_active status of a TornUserProfile.
    """
    if request.method == 'POST':
        profile = get_object_or_404(
            TornUserProfile, 
            id=profile_id, 
            user=request.user
        )
        profile.is_active = not profile.is_active
        profile.save()
        
        status = "activated" if profile.is_active else "deactivated"
        messages.success(
            request, 
            f"API key for {profile.tornuser} has been {status}."
        )
    
    return redirect('users:modify_profile')


@login_required
def delete_profile(request, profile_id):
    """
    Delete a TornUserProfile.
    """
    if request.method == 'POST':
        profile = get_object_or_404(
            TornUserProfile, 
            id=profile_id, 
            user=request.user
        )
        tornuser = profile.tornuser
        profile.delete()
        messages.success(
            request, 
            f"API key for {tornuser} has been deleted."
        )
    
    return redirect('users:modify_profile')


@login_required
def addApiKey(request):
    """
    Add a new TornUserProfile by fetching username from Torn API.
    """
    if request.method == 'POST':
        tornapi = request.POST.get('tornapi', '').strip()
        
        if not tornapi:
            messages.error(request, "Please provide an API key.")
            return redirect('users:modify_profile')
        
        # Check if this exact API key already exists for this user
        if TornUserProfile.objects.filter(user=request.user, tornapi=tornapi).exists():
            messages.error(request, "This exact API key already exists in your account.")
            return redirect('users:modify_profile')
        
        # Fetch username from Torn API
        tornuser, success, error_msg = fetch_torn_username(tornapi)
        
        if success:
            # Always create a new profile - allow multiple keys for the same user
            # This allows users to have different security level keys for the same account
            TornUserProfile.objects.create(
                user=request.user,
                tornuser=tornuser,
                tornapi=tornapi
            )
            
            # Check if this is an additional key for an existing user
            user_key_count = TornUserProfile.objects.filter(
                user=request.user, 
                tornuser=tornuser
            ).count()
            
            if user_key_count > 1:
                messages.success(
                    request, 
                    f"Additional API key for {tornuser} has been added. "
                    f"You now have {user_key_count} keys for this user."
                )
            else:
                messages.success(request, f"API key for {tornuser} has been added.")
        else:
            messages.error(request, f"Failed to fetch username: {error_msg}")
    
    return redirect('users:modify_profile')