from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)


class LoyaltyPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_points')
    points = models.PositiveIntegerField(default=0)

    def add_points(self, amount):
        self.points += amount
        self.save()

    def redeem_points(self, amount):
        if self.points >= amount:
            self.points -= amount
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.user.username} - {self.points} pts"


class Pet(models.Model):
    SPECIES_CHOICES = [
        ('Dog', 'Dog'), ('Cat', 'Cat'), ('Rabbit', 'Rabbit'),
        ('Bird', 'Bird'), ('Other', 'Other'),
    ]
    SIZE_CHOICES = [
        ('Small', 'Small'), ('Medium', 'Medium'), ('Large', 'Large'),
    ]
    AGE_GROUP_CHOICES = [
        ('Baby', 'Baby'), ('Young', 'Young'), ('Adult', 'Adult'), ('Senior', 'Senior'),
    ]
    TEMPERAMENT_CHOICES = [
        ('Calm', 'Calm'), ('Energetic', 'Energetic'),
        ('Friendly', 'Friendly'), ('Shy', 'Shy'),
    ]

    name = models.CharField(max_length=100)
    species = models.CharField(max_length=10, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='Medium')
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES, default='Adult')
    temperament = models.CharField(max_length=10, choices=TEMPERAMENT_CHOICES, default='Friendly')
    good_with_kids = models.BooleanField(default=True)
    good_with_dogs = models.BooleanField(default=True)
    good_with_cats = models.BooleanField(default=True)
    shelter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    shelter_name = models.CharField(max_length=150, blank=True)
    description = models.TextField()
    is_available = models.BooleanField(default=True)
    adoption_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='pets/', blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.species})"


class Adopter(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    home_type = models.CharField(max_length=50, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.full_name


class AdoptionApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adoption_applications',
    )
    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE)
    application_date = models.DateField(auto_now_add=True)
    preferred_meet_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notification = models.TextField(blank=True, null=True)
    redeemed_points = models.PositiveIntegerField(default=0)
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True, help_text="Why do you want to adopt?")

    class Meta:
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.adopter.full_name} → {self.pet.name}"


class SavedLocation(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=User)
def create_user_extras(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        LoyaltyPoints.objects.create(user=instance)


@receiver(post_save, sender=AdoptionApplication)
def send_adoption_status_email(sender, instance, **kwargs):
    if instance.status == 'verified':
        subject = "Adoption Application Approved - PawMatch"
        body = (
            f"Dear {instance.adopter.full_name},\n\n"
            f"Your application to adopt {instance.pet.name} has been approved!\n"
            f"Adoption fee: ${instance.total_amount}\n\n"
            f"Thank you for choosing PawMatch!"
        )
    elif instance.status == 'cancelled':
        subject = "Adoption Application Update - PawMatch"
        body = (
            f"Dear {instance.adopter.full_name},\n\n"
            f"Your application for {instance.pet.name} was not approved at this time.\n"
            f"Please contact the shelter for more information."
        )
    else:
        return

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL or 'noreply@pawmatch.local', [instance.adopter.email], fail_silently=True)
