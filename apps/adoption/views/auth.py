from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from ..forms import AdminRegisterForm, RegisterForm
from ..permissions import is_shelter_staff


class LoginView(FormView):
    template_name = 'adoption/login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        if is_shelter_staff(form.get_user()):
            return redirect('shelter_dashboard')
        return redirect('index')


class RegisterView(FormView):
    template_name = 'adoption/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Account created! Please log in.')
        return super().form_valid(form)


class AdminRegisterView(FormView):
    template_name = 'adoption/register_admin.html'
    form_class = AdminRegisterForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Shelter admin account created! Please log in.')
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    return redirect('landing_page')
