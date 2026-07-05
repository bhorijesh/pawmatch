import json
import time
from datetime import datetime
from decimal import Decimal

import requests
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from .forms import ContactForm, PetForm, RegisterForm
from .models import AdoptionApplication, Adopter, Pet, SavedLocation
from .utils import (
    calculate_distance_view,
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


class AdoptionApplyView(LoginRequiredMixin, View):
    def get(self, request):
        pet = get_object_or_404(Pet, id=request.GET.get('pet_id'))
        points = getattr(getattr(request.user, 'loyalty_points', None), 'points', 0)
        return render(request, 'adoption/apply.html', {'pet': pet, 'loyalty_points': points})

    def post(self, request):
        pet = get_object_or_404(Pet, id=request.POST.get('pet_id'))
        if not pet.is_available:
            return render(request, 'adoption/apply.html', {
                'pet': pet, 'error_message': 'This pet is no longer available.',
            })
        try:
            meet_date = datetime.strptime(request.POST.get('meet_date'), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return render(request, 'adoption/apply.html', {
                'pet': pet, 'error_message': 'Invalid date. Use YYYY-MM-DD.',
            })
        if meet_date < timezone.now().date():
            return render(request, 'adoption/apply.html', {
                'pet': pet, 'error_message': 'Meet date cannot be in the past.',
            })

        base = pet.adoption_fee
        redeem = int(request.POST.get('redeem_points') or 0)
        discount = Decimal('0')
        if redeem and hasattr(request.user, 'loyalty_points'):
            if not request.user.loyalty_points.redeem_points(redeem):
                return render(request, 'adoption/apply.html', {
                    'pet': pet, 'error_message': 'Not enough loyalty points.',
                })
            discount = Decimal(redeem)

        adopter = Adopter.objects.create(
            full_name=request.POST['full_name'],
            email=request.POST['email'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            home_type=request.POST.get('home_type', ''),
            latitude=request.session.get('saved_latitude'),
            longitude=request.session.get('saved_longitude'),
        )
        AdoptionApplication.objects.create(
            pet=pet, user=request.user, adopter=adopter,
            preferred_meet_date=meet_date,
            total_amount=base - discount,
            base_amount=base, discount_amount=discount,
            redeemed_points=redeem,
            message=request.POST.get('message', ''),
        )
        messages.success(request, f'Application submitted for {pet.name}!')
        return redirect('my_applications')


@login_required
def my_applications(request):
    apps = request.user.adoption_applications.all()
    return render(request, 'adoption/my_applications.html', {'applications': apps})


@login_required
def cancel_application(request, app_id):
    app = get_object_or_404(AdoptionApplication, id=app_id, user=request.user)
    if app.status in ('pending', 'verified'):
        app.status = 'cancelled'
        app.save()
        messages.success(request, 'Application cancelled.')
    return redirect('my_applications')


@login_required
def pay_application(request, app_id):
    """Redirect to application confirmation page (Khalti checkout)."""
    application = get_object_or_404(AdoptionApplication, id=app_id, user=request.user)
    if application.status != 'verified':
        messages.error(request, 'You can only pay for approved applications.')
        return redirect('my_applications')
    return redirect('application_confirmation', application_id=application.id)


class ApplicationConfirmationView(LoginRequiredMixin, View):
    def get(self, request, application_id):
        application = get_object_or_404(AdoptionApplication, id=application_id, user=request.user)
        return render(request, 'adoption/application_confirmation.html', {
            'application': application,
            'formatted_amount': f"{application.total_amount:,.2f}".replace(",", ""),
            'khalti_public_key': settings.KHALTI_PUBLIC_KEY,
            'khalti_amount_paisa': int(application.total_amount * 100),
        })


@login_required
def initKhalti(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")

    try:
        application_id = request.POST.get('application_id') or request.POST.get('booking_id')
        application = AdoptionApplication.objects.get(id=application_id, user=request.user)

        order_id = f"ORDER-{application.id}-{int(time.time())}"
        amount = int(application.total_amount * 100)

        payload = {
            "return_url": settings.KHALTI_RETURN_URL,
            "website_url": settings.KHALTI_WEBSITE_URL,
            "amount": amount,
            "purchase_order_id": order_id,
            "purchase_order_name": f"Pet Adoption - {application.pet.name}",
            "customer_info": {
                "name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
                "phone": "9848077880",
            },
        }

        headers = {
            'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        url = f"{settings.KHALTI_API_BASE}epayment/initiate/"

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()

        if response.status_code == 200:
            request.session['payment_order_id'] = order_id
            request.session['application_id'] = application_id
            payment_url = response_data.get('payment_url')

            if payment_url:
                return HttpResponseRedirect(payment_url)
            return JsonResponse({
                'success': False,
                'message': 'Payment URL not found in response',
            })
        error_msg = response_data.get('detail', 'Payment initialization failed')
        return JsonResponse({
            'success': False,
            'message': error_msg,
            'debug_info': response_data,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def verifyKhalti(request):
    if request.method == 'GET':
        url = f"{settings.KHALTI_API_BASE}epayment/lookup/"
        headers = {
            'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        pidx = request.GET.get('pidx')
        if not pidx:
            return redirect('index')

        data = json.dumps({'pidx': pidx})
        response = requests.post(url, headers=headers, data=data)
        new_res = response.json()

        if new_res.get('status') == 'Completed':
            application_id = request.session.get('application_id')
            if not application_id:
                purchase_order_id = request.GET.get('purchase_order_id', '')
                parts = purchase_order_id.split('-', 2)
                if len(parts) >= 2 and parts[0] == 'ORDER':
                    application_id = parts[1]
            if application_id:
                application = get_object_or_404(AdoptionApplication, id=application_id)
                application.status = 'paid'
                application.pet.is_available = False
                application.pet.save()
                application.save()
                if hasattr(application.user, 'loyalty_points'):
                    application.user.loyalty_points.add_points(50)
                messages.success(request, 'Payment successful!')
                return redirect('my_applications')
            return redirect('my_applications')
        return redirect('my_applications')

    return redirect('my_applications')


@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        token = data.get("token")
        amount = data.get("amount")

        headers = {
            "Authorization": f"key {settings.KHALTI_SECRET_KEY}",
        }
        payload = {
            "token": token,
            "amount": amount,
        }

        response = requests.post(
            f"{settings.KHALTI_API_BASE}payment/verify/",
            data=payload,
            headers=headers,
        )
        response_data = response.json()

        if response.status_code == 200:
            return JsonResponse({"message": "Payment Successful", "data": response_data})
        return JsonResponse(
            {"message": "Payment Verification Failed", "data": response_data},
            status=400,
        )

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def process_payment(request, application_id=None, booking_id=None):
    app_id = application_id or booking_id
    application = get_object_or_404(AdoptionApplication, id=app_id, user=request.user)

    if application.status != 'verified':
        messages.error(request, "You can only pay for verified applications.")
        return redirect('my_applications')

    application.status = 'paid'
    application.pet.is_available = False
    application.pet.save()
    application.save()

    messages.success(request, "Payment successful!")
    return redirect('my_applications')


class LoginView(FormView):
    template_name = 'adoption/login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        if form.get_user().is_superuser:
            return redirect('shelter_dashboard')
        return redirect('index')


class RegisterView(FormView):
    template_name = 'adoption/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Account created! Please log in.')
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    return redirect('landing_page')


class AboutView(View):
    def get(self, request):
        return render(request, 'adoption/about.html')


class MapView(View):
    def get(self, request):
        pets = Pet.objects.filter(is_available=True, latitude__isnull=False)
        return render(request, 'adoption/map.html', {'pets': pets})


class ContactView(FormView):
    template_name = 'adoption/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def form_valid(self, form):
        messages.success(self.request, 'Message sent! We will reply soon.')
        return super().form_valid(form)


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


# --- Shelter admin ---

@login_required
def shelter_dashboard(request):
    if not request.user.is_superuser:
        return redirect('index')
    return render(request, 'adoption/shelter/dashboard.html', {
        'pets': Pet.objects.filter(shelter=request.user),
        'applications': AdoptionApplication.objects.filter(pet__shelter=request.user),
        'pending_count': AdoptionApplication.objects.filter(pet__shelter=request.user, status='pending').count(),
    })


@login_required
def shelter_pets(request):
    if not request.user.is_superuser:
        return redirect('index')
    return render(request, 'adoption/shelter/pets.html', {
        'pets': Pet.objects.filter(shelter=request.user),
    })


@login_required
def shelter_applications(request):
    if not request.user.is_superuser:
        return redirect('index')
    return render(request, 'adoption/shelter/applications.html', {
        'applications': AdoptionApplication.objects.filter(pet__shelter=request.user),
    })


@login_required
def review_application(request, app_id):
    if not request.user.is_superuser:
        return redirect('index')
    app = get_object_or_404(AdoptionApplication, id=app_id, pet__shelter=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if app.status == 'pending':
            if action == 'approve':
                app.status = 'verified'
                app.save()
                messages.success(request, 'Application approved.')
            elif action == 'reject':
                app.status = 'cancelled'
                app.save()
                messages.info(request, 'Application rejected.')
        return redirect('shelter_applications')
    return render(request, 'adoption/shelter/application_detail.html', {'application': app})


class PetCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Pet
    form_class = PetForm
    template_name = 'adoption/shelter/pet_form.html'
    success_url = reverse_lazy('shelter_pets')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.shelter = self.request.user
        return super().form_valid(form)


class PetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pet
    form_class = PetForm
    template_name = 'adoption/shelter/pet_form.html'
    success_url = reverse_lazy('shelter_pets')

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return Pet.objects.filter(shelter=self.request.user)


class PetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Pet
    template_name = 'adoption/shelter/pet_confirm_delete.html'
    success_url = reverse_lazy('shelter_pets')

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return Pet.objects.filter(shelter=self.request.user)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password updated.')
            return redirect('shelter_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'adoption/shelter/change_password.html', {'form': form})
