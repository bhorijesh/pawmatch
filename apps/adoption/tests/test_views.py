from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from apps.adoption.models import AdoptionApplication, Adopter, LoyaltyPoints, Pet
from apps.adoption.permissions import SHELTER_STAFF_GROUP, is_shelter_staff


class ShelterPermissionTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name=SHELTER_STAFF_GROUP)
        self.shelter = User.objects.create_user('shelter1', 's@shelter.local', 'pass12345')
        self.shelter.groups.add(self.group)
        self.adopter = User.objects.create_user('adopter2', 'a@example.com', 'pass12345')

    def test_shelter_staff_detected(self):
        self.assertTrue(is_shelter_staff(self.shelter))
        self.assertFalse(is_shelter_staff(self.adopter))


class ApplicationWorkflowTests(TestCase):
    def setUp(self):
        self.shelter = User.objects.create_user('shelter2', 's2@shelter.local', 'pass12345')
        self.adopter = User.objects.create_user('adopter3', 'a3@example.com', 'pass12345')
        LoyaltyPoints.objects.get_or_create(user=self.adopter, defaults={'points': 100})
        self.pet = Pet.objects.create(
            name='TestDog', species='Dog', description='Friendly dog',
            shelter=self.shelter, adoption_fee=Decimal('50'),
        )

    def _create_application(self, status='pending', redeemed=0):
        adopter = Adopter.objects.create(
            full_name='Jane Doe', email='jane@example.com',
            phone='9800000000', address='123 Main St',
        )
        return AdoptionApplication.objects.create(
            pet=self.pet, user=self.adopter, adopter=adopter,
            total_amount=Decimal('50') - Decimal(redeemed),
            base_amount=Decimal('50'), discount_amount=Decimal(redeemed),
            redeemed_points=redeemed, status=status,
        )

    def test_duplicate_application_blocked(self):
        self.client.login(username='adopter3', password='pass12345')
        self._create_application(status='pending')
        url = reverse('apply') + f'?pet_id={self.pet.id}'
        response = self.client.get(url)
        self.assertRedirects(response, reverse('my_applications'))

    def test_cancel_refunds_loyalty_points(self):
        app = self._create_application(redeemed=20)
        points = self.adopter.loyalty_points
        points.points = 80
        points.save()
        self.client.login(username='adopter3', password='pass12345')
        self.client.post(reverse('cancel_application', args=[app.id]))
        points.refresh_from_db()
        self.assertEqual(points.points, 100)
        app.refresh_from_db()
        self.assertEqual(app.status, 'cancelled')

    def test_register_does_not_grant_shelter_access(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_superuser)
        self.assertFalse(is_shelter_staff(user))
