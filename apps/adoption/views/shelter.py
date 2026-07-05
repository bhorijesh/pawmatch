from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from ..forms import PetForm
from ..models import AdoptionApplication, Pet
from ..permissions import is_shelter_staff
from .mixins import ShelterStaffMixin


@login_required
def shelter_dashboard(request):
    if not is_shelter_staff(request.user):
        return redirect('index')
    return render(request, 'adoption/shelter/dashboard.html', {
        'pets': Pet.objects.filter(shelter=request.user),
        'applications': AdoptionApplication.objects.filter(pet__shelter=request.user),
        'pending_count': AdoptionApplication.objects.filter(
            pet__shelter=request.user, status='pending',
        ).count(),
    })


@login_required
def shelter_pets(request):
    if not is_shelter_staff(request.user):
        return redirect('index')
    return render(request, 'adoption/shelter/pets.html', {
        'pets': Pet.objects.filter(shelter=request.user),
    })


@login_required
def shelter_applications(request):
    if not is_shelter_staff(request.user):
        return redirect('index')
    return render(request, 'adoption/shelter/applications.html', {
        'applications': AdoptionApplication.objects.filter(pet__shelter=request.user),
    })


@login_required
def review_application(request, app_id):
    if not is_shelter_staff(request.user):
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
                if app.redeemed_points and hasattr(app.user, 'loyalty_points'):
                    app.user.loyalty_points.add_points(app.redeemed_points)
                app.status = 'cancelled'
                app.save()
                messages.info(request, 'Application rejected.')
        elif app.status == 'paid' and action == 'complete':
            app.status = 'completed'
            app.save()
            messages.success(request, 'Adoption marked as complete.')
        return redirect('shelter_applications')
    return render(request, 'adoption/shelter/application_detail.html', {'application': app})


class PetCreateView(ShelterStaffMixin, CreateView):
    model = Pet
    form_class = PetForm
    template_name = 'adoption/shelter/pet_form.html'
    success_url = reverse_lazy('shelter_pets')

    def form_valid(self, form):
        form.instance.shelter = self.request.user
        return super().form_valid(form)


class PetUpdateView(ShelterStaffMixin, UpdateView):
    model = Pet
    form_class = PetForm
    template_name = 'adoption/shelter/pet_form.html'
    success_url = reverse_lazy('shelter_pets')

    def get_queryset(self):
        return Pet.objects.filter(shelter=self.request.user)


class PetDeleteView(ShelterStaffMixin, DeleteView):
    model = Pet
    template_name = 'adoption/shelter/pet_confirm_delete.html'
    success_url = reverse_lazy('shelter_pets')

    def get_queryset(self):
        return Pet.objects.filter(shelter=self.request.user)


@login_required
def change_password(request):
    if not is_shelter_staff(request.user):
        return redirect('index')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password updated.')
            return redirect('shelter_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'adoption/shelter/change_password.html', {'form': form})
