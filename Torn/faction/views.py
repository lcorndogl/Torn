from django.shortcuts import render
from django.db.models import Count
from users.models import UserRecord
from .models import FactionList
from datetime import datetime, timedelta


def faction_comparison(request):
    factions = FactionList.objects.all().order_by(
        'name')  # Sort factions alphabetically
    default_faction1 = None
    default_faction2 = None

    # Fetch the faction for user ID 2908770
    user_record = UserRecord.objects.filter(user_id=2908770).first()
    if user_record:
        default_faction1 = user_record.current_faction_id

        # Fetch the faction at war with the user's faction (if available)
        war_faction = FactionList.objects.filter(
            faction_id=user_record.current_faction_id).first()
        # Assuming a relationship exists
        if war_faction and hasattr(war_faction, 'at_war_with'):
            default_faction2 = war_faction.at_war_with.faction_id

    # Calculate the timestamp for 7 days ago
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    seven_days_ago_timestamp = seven_days_ago.timestamp()

    faction1_data = {}
    faction2_data = {}
    faction1_users = {}
    faction2_users = {}
    faction1_name = ""
    faction2_name = ""
    max_value = 0
    max_delta = 0  # Initialize max_delta

    if request.method == 'POST':
        faction1_id = request.POST.get('faction1')
        faction2_id = request.POST.get('faction2')

        if faction1_id and faction2_id:
            faction1_name = FactionList.objects.get(
                faction_id=faction1_id).name
            faction2_name = FactionList.objects.get(
                faction_id=faction2_id).name

            # Filter records for the last 7 days
            faction1_records = UserRecord.objects.filter(
                current_faction_id=faction1_id, last_action_timestamp__gte=seven_days_ago_timestamp)
            faction2_records = UserRecord.objects.filter(
                current_faction_id=faction2_id, last_action_timestamp__gte=seven_days_ago_timestamp)

            faction1_seen = set()
            faction2_seen = set()

            for record in faction1_records:
                date_hour = datetime.fromtimestamp(
                    record.last_action_timestamp).strftime('%Y-%m-%d %a %H:00')
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
                date_hour = datetime.fromtimestamp(
                    record.last_action_timestamp).strftime('%Y-%m-%d %a %H:00')
                if (date_hour, record.user_id_id) not in faction2_seen:
                    faction2_seen.add((date_hour, record.user_id_id))
                    if date_hour in faction2_data:
                        faction2_data[date_hour] += 1
                        faction2_users[date_hour].append(record.user_id_id)
                    else:
                        faction2_data[date_hour] = 1
                        faction2_users[date_hour] = [record.user_id_id]
                    max_value = max(max_value, faction2_data[date_hour])

            # Calculate max_delta
            all_date_hours = sorted(set(faction1_data.keys()).union(
                set(faction2_data.keys())), reverse=True)
            for date_hour in all_date_hours:
                faction1_count = faction1_data.get(date_hour, 0)
                faction2_count = faction2_data.get(date_hour, 0)
                max_delta = max(max_delta, abs(
                    faction1_count - faction2_count))

            print("Faction 1 Data:", faction1_data)
            print("Faction 2 Data:", faction2_data)
            print("Date Hours:", all_date_hours)
            print("Max Delta:", max_delta)

    context = {
        'factions': factions,
        'default_faction1': default_faction1,
        'default_faction2': default_faction2,
        'faction1_data': faction1_data,
        'faction2_data': faction2_data,
        'faction1_users': faction1_users,
        'faction2_users': faction2_users,
        'faction1_name': faction1_name,
        'faction2_name': faction2_name,
        'max_value': max_value,
        'max_delta': max_delta,  # Add max_delta to the context
        'date_hours': sorted(set(faction1_data.keys()).union(set(faction2_data.keys())), reverse=True),
    }
    return render(request, 'faction/faction_comparison.html', context)
