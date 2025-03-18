from django.shortcuts import render
from .models import Racket, Territory
from datetime import datetime

def rackets_list(request):
    rackets_data = []
    seen_territory_codes = set()  # Keep track of territory codes we've seen
    max_records = 25
    record_count = 0

    for racket in Racket.objects.all().order_by('-timestamp'): # Order by timestamp descending
        if record_count >= max_records:
            break  # Stop if we've reached the maximum number of records

        if racket.territory.code not in seen_territory_codes:
            rackets_data.append({
                'racket': racket,
                'timestamp': datetime.now()
            })
            seen_territory_codes.add(racket.territory.code)
            record_count += 1

    print("rackets_data:", rackets_data)  # Keep this for debugging
    return render(request, 'racket/racket.html', {'rackets': rackets_data})
