"""Seed sample pets and a shelter admin account."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User

from apps.adoption.models import Pet
from apps.adoption.permissions import SHELTER_STAFF_GROUP


SAMPLE_PETS = [
    {
        'name': 'Buddy', 'species': 'Dog', 'breed': 'Golden Retriever',
        'size': 'Large', 'age_group': 'Adult', 'temperament': 'Friendly',
        'shelter_name': 'Happy Paws Shelter', 'adoption_fee': 75,
        'latitude': 27.7172, 'longitude': 85.3240,
        'description': 'Buddy loves walks and is great with kids. Fully vaccinated.',
    },
    {
        'name': 'Luna', 'species': 'Cat', 'breed': 'Domestic Shorthair',
        'size': 'Small', 'age_group': 'Young', 'temperament': 'Calm',
        'shelter_name': 'Happy Paws Shelter', 'adoption_fee': 50,
        'latitude': 27.7200, 'longitude': 85.3300,
        'description': 'Luna is a gentle indoor cat who loves sunny windowsills.',
    },
    {
        'name': 'Max', 'species': 'Dog', 'breed': 'Labrador Mix',
        'size': 'Medium', 'age_group': 'Young', 'temperament': 'Energetic',
        'shelter_name': 'Valley Animal Rescue', 'adoption_fee': 60,
        'latitude': 27.7100, 'longitude': 85.3150,
        'description': 'Max is playful and learns quickly. Good with other dogs.',
    },
    {
        'name': 'Whiskers', 'species': 'Cat', 'breed': 'Persian',
        'size': 'Medium', 'age_group': 'Senior', 'temperament': 'Shy',
        'shelter_name': 'Valley Animal Rescue', 'adoption_fee': 0,
        'latitude': 27.7050, 'longitude': 85.3200,
        'description': 'Whiskers needs a quiet home. Very affectionate once comfortable.',
        'good_with_kids': False,
    },
    {
        'name': 'Cottontail', 'species': 'Rabbit', 'breed': 'Holland Lop',
        'size': 'Small', 'age_group': 'Baby', 'temperament': 'Calm',
        'shelter_name': 'Small Friends Sanctuary', 'adoption_fee': 25,
        'latitude': 27.7250, 'longitude': 85.3100,
        'description': 'Adorable rabbit looking for a loving indoor home.',
        'good_with_dogs': False, 'good_with_cats': False,
    },
    {
        'name': 'Rocky', 'species': 'Dog', 'breed': 'Beagle',
        'size': 'Medium', 'age_group': 'Adult', 'temperament': 'Friendly',
        'shelter_name': 'Happy Paws Shelter', 'adoption_fee': 55,
        'latitude': 27.7150, 'longitude': 85.3280,
        'description': 'Rocky has a great nose and loves outdoor adventures.',
    },
]


class Command(BaseCommand):
    help = 'Create shelter admin and sample pets for demo'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=SHELTER_STAFF_GROUP)

        admin, created = User.objects.get_or_create(
            username='shelteradmin',
            defaults={'email': 'admin@shelter.local', 'is_superuser': True, 'is_staff': True},
        )
        if created:
            admin.set_password('admin12345')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created shelter admin: shelteradmin / admin12345'))
        else:
            self.stdout.write('Shelter admin already exists.')
        admin.groups.add(group)

        adopter, created_adopter = User.objects.get_or_create(
            username='adopter1',
            defaults={'email': 'adopter@example.com'},
        )
        if created_adopter:
            adopter.set_password('adopter123')
            adopter.save()
            self.stdout.write(self.style.SUCCESS('Created adopter: adopter1 / adopter123'))

        for data in SAMPLE_PETS:
            defaults = {k: v for k, v in data.items()}
            name = defaults.pop('name')
            Pet.objects.get_or_create(name=name, shelter=admin, defaults=defaults)

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(SAMPLE_PETS)} sample pets.'))
