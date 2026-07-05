from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.decorators.http import require_POST

from ..forms import AdoptionApplicationForm
from ..models import AdoptionApplication, Adopter, Pet
from .mixins import application_form_initial, has_active_application


class AdoptionApplyView(LoginRequiredMixin, View):
    def get(self, request):
        pet = get_object_or_404(Pet, id=request.GET.get('pet_id'))
        if has_active_application(request.user, pet):
            messages.error(request, f'You already have an active application for {pet.name}.')
            return redirect('my_applications')
        points = getattr(getattr(request.user, 'loyalty_points', None), 'points', 0)
        form = AdoptionApplicationForm(initial=application_form_initial(request.user))
        return render(request, 'adoption/apply.html', {
            'pet': pet, 'loyalty_points': points, 'form': form,
        })

    def post(self, request):
        pet = get_object_or_404(Pet, id=request.POST.get('pet_id'))
        if not pet.is_available:
            return render(request, 'adoption/apply.html', {
                'pet': pet,
                'form': AdoptionApplicationForm(request.POST),
                'error_message': 'This pet is no longer available.',
            })
        if has_active_application(request.user, pet):
            messages.error(request, f'You already have an active application for {pet.name}.')
            return redirect('my_applications')

        form = AdoptionApplicationForm(request.POST)
        if not form.is_valid():
            points = getattr(getattr(request.user, 'loyalty_points', None), 'points', 0)
            return render(request, 'adoption/apply.html', {
                'pet': pet, 'form': form, 'loyalty_points': points,
            })

        base = pet.adoption_fee
        redeem = form.cleaned_data['redeem_points']
        discount = Decimal('0')
        if redeem and hasattr(request.user, 'loyalty_points'):
            if not request.user.loyalty_points.redeem_points(redeem):
                points = request.user.loyalty_points.points
                form.add_error('redeem_points', 'Not enough loyalty points.')
                return render(request, 'adoption/apply.html', {
                    'pet': pet, 'form': form, 'loyalty_points': points,
                })
            discount = Decimal(redeem)

        adopter = Adopter.objects.create(
            full_name=form.cleaned_data['full_name'],
            email=form.cleaned_data['email'],
            phone=form.cleaned_data['phone'],
            address=form.cleaned_data['address'],
            home_type=form.cleaned_data['home_type'],
            latitude=request.session.get('saved_latitude'),
            longitude=request.session.get('saved_longitude'),
        )
        AdoptionApplication.objects.create(
            pet=pet, user=request.user, adopter=adopter,
            preferred_meet_date=form.cleaned_data['meet_date'],
            total_amount=base - discount,
            base_amount=base, discount_amount=discount,
            redeemed_points=redeem,
            message=form.cleaned_data.get('message', ''),
        )

        profile = getattr(request.user, 'profile', None)
        if profile:
            profile.phone_number = form.cleaned_data['phone']
            profile.address = form.cleaned_data['address']
            profile.save(update_fields=['phone_number', 'address'])

        messages.success(request, f'Application submitted for {pet.name}!')
        return redirect('my_applications')


@login_required
def my_applications(request):
    apps = request.user.adoption_applications.all()
    return render(request, 'adoption/my_applications.html', {'applications': apps})


@login_required
@require_POST
def cancel_application(request, app_id):
    app = get_object_or_404(AdoptionApplication, id=app_id, user=request.user)
    if app.status in ('pending', 'verified'):
        if app.redeemed_points and hasattr(request.user, 'loyalty_points'):
            request.user.loyalty_points.add_points(app.redeemed_points)
        app.status = 'cancelled'
        app.save()
        messages.success(request, 'Application cancelled.')
    return redirect('my_applications')


@login_required
def pay_application(request, app_id):
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
