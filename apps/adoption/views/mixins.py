from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from ..models import AdoptionApplication
from ..permissions import is_shelter_staff


class ShelterStaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return is_shelter_staff(self.request.user)


def application_form_initial(user):
    profile = getattr(user, 'profile', None)
    return {
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'phone': profile.phone_number if profile and profile.phone_number else '',
        'address': profile.address if profile and profile.address else '',
    }


def has_active_application(user, pet):
    return AdoptionApplication.objects.filter(
        user=user,
        pet=pet,
        status__in=('pending', 'verified', 'paid'),
    ).exists()
