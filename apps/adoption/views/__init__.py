from .applications import (
    AdoptionApplyView,
    ApplicationConfirmationView,
    cancel_application,
    my_applications,
    pay_application,
)
from .auth import AdminRegisterView, LoginView, RegisterView, logout_view
from .location import save_location
from .pages import AboutView, ContactView
from .payments import initKhalti, verifyKhalti, verify_payment
from .pets import (
    HomeView,
    MapView,
    PetListView,
    landing_page,
    nearby_pets,
    pet_detail,
    pet_search,
    recommend_pets,
)
from .shelter import (
    PetCreateView,
    PetDeleteView,
    PetUpdateView,
    change_password,
    review_application,
    shelter_applications,
    shelter_dashboard,
    shelter_pets,
)

__all__ = [
    'AboutView',
    'AdminRegisterView',
    'AdoptionApplyView',
    'ApplicationConfirmationView',
    'ContactView',
    'HomeView',
    'LoginView',
    'MapView',
    'PetCreateView',
    'PetDeleteView',
    'PetListView',
    'PetUpdateView',
    'RegisterView',
    'cancel_application',
    'change_password',
    'initKhalti',
    'landing_page',
    'logout_view',
    'my_applications',
    'nearby_pets',
    'pay_application',
    'pet_detail',
    'pet_search',
    'recommend_pets',
    'review_application',
    'save_location',
    'shelter_applications',
    'shelter_dashboard',
    'shelter_pets',
    'verifyKhalti',
    'verify_payment',
]
