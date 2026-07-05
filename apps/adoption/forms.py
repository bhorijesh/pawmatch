from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Pet


class RegisterForm(UserCreationForm):
    is_shelter_admin = forms.BooleanField(required=False, label="Register as Shelter Admin")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_shelter_admin']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('is_shelter_admin'):
            user.is_superuser = True
            user.is_staff = True
        if commit:
            user.save()
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
