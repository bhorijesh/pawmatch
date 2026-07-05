from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Pet
from .permissions import SHELTER_STAFF_GROUP


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email


class AdminRegisterForm(RegisterForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name=SHELTER_STAFF_GROUP)
            user.groups.add(group)
        return user


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            'name', 'species', 'breed', 'size', 'age_group', 'temperament',
            'good_with_kids', 'good_with_dogs', 'good_with_cats',
            'shelter_name', 'description', 'adoption_fee', 'is_available',
            'image', 'latitude', 'longitude',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'latitude': forms.NumberInput(attrs={'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'step': 'any'}),
        }


HOME_TYPE_CHOICES = [
    ('House', 'House'),
    ('Apartment', 'Apartment'),
    ('Condo', 'Condo'),
    ('Other', 'Other'),
]


class AdoptionApplicationForm(forms.Form):
    full_name = forms.CharField(max_length=255)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    home_type = forms.ChoiceField(choices=HOME_TYPE_CHOICES, initial='House')
    meet_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Preferred Meet & Greet Date',
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Why do you want to adopt this pet?',
    )
    redeem_points = forms.IntegerField(min_value=0, required=False, initial=0)

    def clean_meet_date(self):
        meet_date = self.cleaned_data['meet_date']
        if meet_date < timezone.now().date():
            raise ValidationError('Meet date cannot be in the past.')
        return meet_date

    def clean_redeem_points(self):
        redeem = self.cleaned_data.get('redeem_points') or 0
        pet_id = self.data.get('pet_id')
        if redeem and pet_id:
            pet = Pet.objects.filter(pk=pet_id).first()
            if pet and Decimal(redeem) > pet.adoption_fee:
                raise ValidationError(
                    'Redeemed points cannot exceed the adoption fee.'
                )
        return redeem
