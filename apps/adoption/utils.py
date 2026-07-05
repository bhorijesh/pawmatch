"""Location and recommendation utilities (Haversine + Cosine similarity)."""
from math import radians, sin, cos, sqrt, atan2

from django.http import JsonResponse

from .models import Pet


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


def extract_pet_features(pets):
    """One-hot encode species, size, age_group, temperament into feature vectors."""
    species_list = ['Dog', 'Cat', 'Rabbit', 'Bird', 'Other']
    size_list = ['Small', 'Medium', 'Large']
    age_list = ['Baby', 'Young', 'Adult', 'Senior']
    temperament_list = ['Calm', 'Energetic', 'Friendly', 'Shy']

    features = []
    for pet in pets:
        species_vec = [1 if pet['species'] == s else 0 for s in species_list]
        size_vec = [1 if pet['size'] == s else 0 for s in size_list]
        age_vec = [1 if pet['age_group'] == a else 0 for a in age_list]
        temp_vec = [1 if pet['temperament'] == t else 0 for t in temperament_list]
        features.append(species_vec + size_vec + age_vec + temp_vec)
    return features


def cosine_similarity(vec1, vec2):
    dot = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    mag1 = sum(v ** 2 for v in vec1) ** 0.5
    mag2 = sum(v ** 2 for v in vec2) ** 0.5
    if mag1 == 0 or mag2 == 0:
        return 0
    return dot / (mag1 * mag2)


def get_species_frequencies(adopted_pets):
    freq = {}
    for pet in adopted_pets:
        freq[pet['species']] = freq.get(pet['species'], 0) + 1
    return freq


def content_based_recommendation(user_pets, all_pets, top_n=10):
    """Recommend pets using cosine similarity on adoption history."""
    if not user_pets or not all_pets:
        return []

    user_features = extract_pet_features(user_pets)
    all_features = extract_pet_features(all_pets)
    species_freq = get_species_frequencies(user_pets)

    scores = []
    for i, pet_feat in enumerate(all_features):
        pet = all_pets[i]
        avg_sim = sum(
            cosine_similarity(uf, pet_feat) for uf in user_features
        ) / len(user_features)
        if pet['species'] in species_freq:
            avg_sim *= (1 + species_freq[pet['species']] * 0.2)
        scores.append((i, avg_sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [all_pets[i] for i, _ in scores[:top_n]]


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
