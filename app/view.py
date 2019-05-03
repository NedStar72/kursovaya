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
from .models import User, Subject, Specialty, Group, StudentTeacherSubject
import app.forms

from braces import views


class HomeView(LoginRequiredMixin, CreateView):
    form_class = app.forms.TeacherSignUpForm  # изменить форму
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        context['title'] = 'Главная странциа'
        context['year'] = datetime.now().year
        return context


class SubjectAddFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "subject_add.html"
    model = Subject
    form_class = app.forms.SubjectAddForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Добавить предмет'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('/')


class SpecialityAddFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "subject_add.html"
    model = Specialty
    form_class = app.forms.SpecialtyAddForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Добавить направление'
        return super().get_context_data(**kwargs)


class GroupAddFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "group_add.html"
    model = Group
    form_class = app.forms.GroupAddForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Добавить группу'
        return super().get_context_data(**kwargs)


class RegisterView(LoginRequiredMixin, views.SuperuserRequiredMixin, TemplateView):
    template_name = 'registration/signup.html'

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Регистрация'
        kwargs['year'] = datetime.now().year
        return super(RegisterView, self).get_context_data()


class StudentRegisterFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "registration/s_registration.html"
    model = User
    form_class = app.forms.StudentSignUpForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Регистрация студента'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('/admin')


class TeacherRegisterFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "registration/t_registration.html"
    model = User
    form_class = app.forms.TeacherSignUpForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Регистрация преподавателя'
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


class CourseAddFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "group_add.html"
    model = StudentTeacherSubject
    form_class = app.forms.CourseAddForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Добавить курс'
        return super().get_context_data(**kwargs)
