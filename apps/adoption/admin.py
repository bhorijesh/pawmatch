from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Pet, Adopter, AdoptionApplication, UserProfile, LoyaltyPoints


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'size', 'is_available', 'shelter_name')
    list_filter = ('species', 'size', 'age_group', 'is_available')
    search_fields = ('name', 'breed', 'shelter_name')


@admin.register(Adopter)
class AdopterAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'home_type')


@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('adopter', 'pet', 'status', 'application_date', 'total_amount')
    list_filter = ('status',)
    actions = ['approve_applications']

    @admin.action(description='Approve selected applications')
    def approve_applications(self, request, queryset):
        queryset.update(status='verified')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class LoyaltyInline(admin.StackedInline):
    model = LoyaltyPoints
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, LoyaltyInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.site_header = 'PawMatch Administration'
admin.site.site_title = 'PawMatch Admin'
