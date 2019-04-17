from datetime import datetime

from django.http import Http404
from django.http import HttpRequest
from django.template import RequestContext
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login

from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView

from django.contrib.auth.forms import UserCreationForm
from .models import User
import app.forms

from braces import views


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        context['title'] = 'Главная странциа'
        context['year'] = datetime.now().year
        return context


class RegisterView(LoginRequiredMixin, views.SuperuserRequiredMixin, TemplateView):
    template_name = 'signup.html'

    def get_context_data(self, **kwargs):
        context = super(RegisterView, self).get_context_data()
        context['title'] = 'Регистрация'
        context['year'] = datetime.now().year
        return context


class StudentRegisterFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "registration/s_registration.html"
    model = User
    form_class = app.forms.StudentSignUpForm

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('/admin')


class MyLoginView(LoginView):
    authentication_form = app.forms.AuthForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super(MyLoginView, self).get_context_data()
        context['title'] = 'Страница входа'
        context['year'] = datetime.now().year
        return context

    def form_valid(self, form):
        if form.cleaned_data['checkbox']:
            self.request.session.set_expiry(0)
        return super(MyLoginView, self).form_valid(form)
