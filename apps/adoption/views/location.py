import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..models import SavedLocation


@csrf_exempt
def save_location(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        lat, lon = data.get('latitude'), data.get('longitude')
        if lat is None or lon is None:
            return JsonResponse({'error': 'Missing coordinates'}, status=400)
        request.session['saved_latitude'] = lat
        request.session['saved_longitude'] = lon
        SavedLocation.objects.create(latitude=lat, longitude=lon)
        return JsonResponse({'message': 'Location saved!'})
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid data'}, status=400)
