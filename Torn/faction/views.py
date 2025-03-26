from django.shortcuts import render
from django.db.models import Count
from users.models import UserRecord
from .models import FactionList
from datetime import datetime, timedelta

def faction_comparison(request):
    factions = FactionList.objects.all()
    faction1_data = {}
    faction2_data = {}
    faction1_users = {}
    faction2_users = {}
    faction1_name = ""
    faction2_name = ""
    max_value = 0

    if request.method == 'POST':
        faction1_id = request.POST.get('faction1')
        faction2_id = request.POST.get('faction2')

        if faction1_id and faction2_id:
            faction1_name = FactionList.objects.get(faction_id=faction1_id).name
            faction2_name = FactionList.objects.get(faction_id=faction2_id).name

            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            faction1_records = UserRecord.objects.filter(current_faction_id=faction1_id, last_action_timestamp__gte=seven_days_ago.timestamp())
            faction2_records = UserRecord.objects.filter(current_faction_id=faction2_id, last_action_timestamp__gte=seven_days_ago.timestamp())

            faction1_seen = set()
            faction2_seen = set()

            for record in faction1_records:
                date_hour = datetime.fromtimestamp(record.last_action_timestamp).strftime('%Y-%m-%d %a %H:00')
                if (date_hour, record.user_id_id) not in faction1_seen:
                    faction1_seen.add((date_hour, record.user_id_id))
                    if date_hour in faction1_data:
                        faction1_data[date_hour] += 1
                        faction1_users[date_hour].append(record.user_id_id)
                    else:
                        faction1_data[date_hour] = 1
                        faction1_users[date_hour] = [record.user_id_id]
                    max_value = max(max_value, faction1_data[date_hour])

            for record in faction2_records:
                date_hour = datetime.fromtimestamp(record.last_action_timestamp).strftime('%Y-%m-%d %a %H:00')
                if (date_hour, record.user_id_id) not in faction2_seen:
                    faction2_seen.add((date_hour, record.user_id_id))
                    if date_hour in faction2_data:
                        faction2_data[date_hour] += 1
                        faction2_users[date_hour].append(record.user_id_id)
                    else:
                        faction2_data[date_hour] = 1
                        faction2_users[date_hour] = [record.user_id_id]
                    max_value = max(max_value, faction2_data[date_hour])

    context = {
        'factions': factions,
        'faction1_data': faction1_data,
        'faction2_data': faction2_data,
        'faction1_users': faction1_users,
        'faction2_users': faction2_users,
        'faction1_name': faction1_name,
        'faction2_name': faction2_name,
        'max_value': max_value,
        'date_hours': sorted(set(faction1_data.keys()).union(set(faction2_data.keys())), reverse=True),
    }
    return render(request, 'faction/faction_comparison.html', context)
