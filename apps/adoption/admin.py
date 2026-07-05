import csv

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Pet, Adopter, AdoptionApplication, UserProfile, LoyaltyPoints, SavedLocation, ContactMessage


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'size', 'is_available', 'shelter_name', 'image_preview')
    list_filter = ('species', 'size', 'age_group', 'is_available', 'temperament')
    search_fields = ('name', 'breed', 'shelter_name')
    readonly_fields = ('image_preview', 'created_at')
    autocomplete_fields = ('shelter',)

    @admin.display(description='Photo')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:60px;border-radius:4px;" />', obj.image.url)
        return '—'


@admin.register(Adopter)
class AdopterAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'home_type')
    search_fields = ('full_name', 'email', 'phone')


@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'adopter', 'pet', 'shelter_name', 'status', 'application_date', 'total_amount')
    list_filter = ('status', 'application_date', 'pet__species')
    search_fields = ('adopter__full_name', 'adopter__email', 'pet__name')
    date_hierarchy = 'application_date'
    autocomplete_fields = ('pet', 'user', 'adopter')
    readonly_fields = ('application_date',)
    actions = ['approve_applications', 'reject_applications', 'mark_completed', 'export_as_csv']

    @admin.display(description='Shelter')
    def shelter_name(self, obj):
        return obj.pet.shelter_name or obj.pet.shelter.username

    @admin.action(description='Approve selected applications')
    def approve_applications(self, request, queryset):
        queryset.filter(status='pending').update(status='verified')

    @admin.action(description='Reject selected applications')
    def reject_applications(self, request, queryset):
        for app in queryset.filter(status='pending'):
            if app.redeemed_points and hasattr(app.user, 'loyalty_points'):
                app.user.loyalty_points.add_points(app.redeemed_points)
            app.status = 'cancelled'
            app.save()

    @admin.action(description='Mark selected as completed')
    def mark_completed(self, request, queryset):
        queryset.filter(status='paid').update(status='completed')

    @admin.action(description='Export selected as CSV')
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="applications.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Adopter', 'Pet', 'Status', 'Date', 'Amount'])
        for app in queryset:
            writer.writerow([
                app.id, app.adopter.full_name, app.pet.name,
                app.status, app.application_date, app.total_amount,
            ])
        return response


@admin.register(SavedLocation)
class SavedLocationAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'message', 'created_at')


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
