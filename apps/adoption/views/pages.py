from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView

from ..forms import ContactForm
from ..models import ContactMessage


class AboutView(View):
    def get(self, request):
        return render(request, 'adoption/about.html')


class ContactView(FormView):
    template_name = 'adoption/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def form_valid(self, form):
        ContactMessage.objects.create(
            name=form.cleaned_data['name'],
            email=form.cleaned_data['email'],
            message=form.cleaned_data['message'],
        )
        send_mail(
            subject=f"PawMatch contact from {form.cleaned_data['name']}",
            message=form.cleaned_data['message'],
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@pawmatch.local',
            recipient_list=[settings.DEFAULT_FROM_EMAIL or 'admin@shelter.local'],
            fail_silently=True,
        )
        messages.success(self.request, 'Message sent! We will reply soon.')
        return super().form_valid(form)
