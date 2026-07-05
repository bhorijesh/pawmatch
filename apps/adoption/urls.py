from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views
from .views import HomeView, PetListView, LoginView, RegisterView, ContactView
from .views import AboutView, MapView, PetCreateView, PetUpdateView, PetDeleteView, AdoptionApplyView
from .views import ApplicationConfirmationView
from .utils import calculate_distance_view

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('index/', HomeView.as_view(), name='index'),
    path('pets/', PetListView.as_view(), name='pet_list'),
    path('pet/<int:pet_id>/', views.pet_detail, name='pet_detail'),
    path('search/', views.pet_search, name='pet_search'),
    path('recommend/', views.recommend_pets, name='recommend_pets'),
    path('nearby/', views.nearby_pets, name='nearby_pets'),
    path('save-location/', views.save_location, name='save_location'),
    path('calculate-distance/', calculate_distance_view, name='calculate_distance'),
    path('apply/', AdoptionApplyView.as_view(), name='apply'),
    path('my-applications/', login_required(views.my_applications), name='my_applications'),
    path('applications/<int:app_id>/cancel/', login_required(views.cancel_application), name='cancel_application'),
    path('applications/<int:app_id>/pay/', login_required(views.pay_application), name='pay_application'),
    path('applications/pay/<int:application_id>/', views.process_payment, name='process_payment'),
    path('applications/confirmation/<int:application_id>/', ApplicationConfirmationView.as_view(), name='application_confirmation'),
    path('init-khalti/', views.initKhalti, name='initkhalti'),
    path('verify-khalti/', views.verifyKhalti, name='verifykhalti'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', AboutView.as_view(), name='about'),
    path('map/', MapView.as_view(), name='map'),
    path('contact/', ContactView.as_view(), name='contact'),
    # Shelter admin
    path('shelter/', login_required(views.shelter_dashboard), name='shelter_dashboard'),
    path('shelter/pets/', login_required(views.shelter_pets), name='shelter_pets'),
    path('shelter/pets/add/', PetCreateView.as_view(), name='pet_create'),
    path('shelter/pets/<int:pk>/edit/', PetUpdateView.as_view(), name='pet_edit'),
    path('shelter/pets/<int:pk>/delete/', PetDeleteView.as_view(), name='pet_delete'),
    path('shelter/applications/', login_required(views.shelter_applications), name='shelter_applications'),
    path('shelter/applications/<int:app_id>/', login_required(views.review_application), name='review_application'),
    path('shelter/change-password/', login_required(views.change_password), name='change_password'),
]
