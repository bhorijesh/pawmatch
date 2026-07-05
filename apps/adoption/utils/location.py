"""Location utilities (Haversine distance)."""
from math import radians, sin, cos, sqrt, atan2

from django.http import JsonResponse

from ..models import Pet


def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance between two GPS points in kilometers."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def calculate_distance_view(request):
    from_lat = float(request.GET.get('from_lat'))
    from_lon = float(request.GET.get('from_lon'))
    to_lat = float(request.GET.get('to_lat'))
    to_lon = float(request.GET.get('to_lon'))
    return JsonResponse({'distance': round(haversine(from_lat, from_lon, to_lat, to_lon), 2)})


def pet_to_dict(pet, distance=None):
    data = {
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'breed': pet.breed,
        'size': pet.size,
        'age_group': pet.age_group,
        'temperament': pet.temperament,
        'good_with_kids': pet.good_with_kids,
        'good_with_dogs': pet.good_with_dogs,
        'good_with_cats': pet.good_with_cats,
        'adoption_fee': str(pet.adoption_fee),
        'is_available': pet.is_available,
        'description': pet.description,
        'image_url': pet.image.url if pet.image else '',
        'latitude': pet.latitude,
        'longitude': pet.longitude,
        'shelter_name': pet.shelter_name,
    }
    if distance is not None:
        data['distance'] = round(distance, 2)
    return data


def get_nearby_pets(latitude, longitude, max_km=50):
    pets = Pet.objects.filter(is_available=True)
    results = []
    for pet in pets:
        if pet.latitude is None or pet.longitude is None:
            continue
        dist = haversine(latitude, longitude, pet.latitude, pet.longitude)
        if dist <= max_km:
            results.append(pet_to_dict(pet, dist))
    results.sort(key=lambda x: x['distance'])
    return results
