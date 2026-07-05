from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import ListView

from ..models import AdoptionApplication, Pet
from ..utils import (
    content_based_recommendation,
    get_nearby_pets,
    haversine,
    pet_to_dict,
)


def landing_page(request):
    return render(request, 'adoption/landing.html')


class HomeView(ListView):
    model = Pet
    template_name = 'adoption/index.html'
    context_object_name = 'pets'


def recommend_pets(request):
    if not request.user.is_authenticated:
        top = (
            AdoptionApplication.objects.values('pet')
            .annotate(c=Count('pet')).order_by('-c')[:3]
        )
        pets = [pet_to_dict(Pet.objects.get(id=t['pet'])) for t in top if Pet.objects.filter(id=t['pet']).exists()]
        return JsonResponse({'recommended_pets': pets})

    history = request.user.adoption_applications.exclude(status='cancelled')
    if history.exists():
        user_pets = [
            {'species': a.pet.species, 'size': a.pet.size,
             'age_group': a.pet.age_group, 'temperament': a.pet.temperament, 'id': a.pet.id}
            for a in history
        ]
        all_pets = [
            {'id': p.id, 'species': p.species, 'size': p.size,
             'age_group': p.age_group, 'temperament': p.temperament}
            for p in Pet.objects.filter(is_available=True)
        ]
        rec_ids = [p['id'] for p in content_based_recommendation(user_pets, all_pets, top_n=3)]
        recommended = [pet_to_dict(p) for p in Pet.objects.filter(id__in=rec_ids)]
        return JsonResponse({'recommended_pets': recommended})

    top = AdoptionApplication.objects.values('pet').annotate(c=Count('pet')).order_by('-c')[:3]
    pets = [pet_to_dict(Pet.objects.get(id=t['pet'])) for t in top if Pet.objects.filter(id=t['pet']).exists()]
    return JsonResponse({'recommended_pets': pets})


def nearby_pets(request):
    try:
        lat = float(request.GET.get('latitude'))
        lon = float(request.GET.get('longitude'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    return JsonResponse({'pets': get_nearby_pets(lat, lon)})


def pet_detail(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    distance = None
    lat = request.session.get('saved_latitude')
    lon = request.session.get('saved_longitude')
    if lat and lon and pet.latitude and pet.longitude:
        try:
            distance = round(haversine(float(lat), float(lon), pet.latitude, pet.longitude), 2)
        except (TypeError, ValueError):
            pass
    return render(request, 'adoption/pet_detail.html', {'pet': pet, 'distance': distance})


def pet_search(request):
    q = request.GET.get('search', '')
    pets = Pet.objects.filter(is_available=True)
    if q:
        pets = pets.filter(name__icontains=q) | pets.filter(breed__icontains=q) | pets.filter(species__icontains=q)
    return render(request, 'adoption/search_results.html', {'pets': pets, 'query': q})


class PetListView(ListView):
    model = Pet
    template_name = 'adoption/pet_list.html'
    context_object_name = 'pets'
    paginate_by = 12

    def get_queryset(self):
        qs = Pet.objects.filter(is_available=True)
        lat = self.request.session.get('saved_latitude')
        lon = self.request.session.get('saved_longitude')
        if not lat or not lon:
            return qs
        try:
            lat, lon = float(lat), float(lon)
        except ValueError:
            return qs
        pets = list(qs)
        for p in pets:
            if p.latitude and p.longitude:
                p.distance = haversine(lat, lon, p.latitude, p.longitude)
            else:
                p.distance = None
        with_dist = [p for p in pets if p.distance is not None]
        return sorted(with_dist, key=lambda p: p.distance) if with_dist else pets


class MapView(View):
    def get(self, request):
        pets = Pet.objects.filter(is_available=True, latitude__isnull=False)
        return render(request, 'adoption/map.html', {'pets': pets})
