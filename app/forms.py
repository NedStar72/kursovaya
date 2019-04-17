from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import Student, Teacher, User


class AuthForm(AuthenticationForm):
    username = forms.CharField(required=True, max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control form-control-lg mb-4',
                                   'placeholder': 'Логин',
                                   'autocomplete': '',
                               }))
    password = forms.CharField(required=True, max_length=254,
                               widget=forms.PasswordInput({
                                   'class': 'form-control form-control-lg mb-4',
                                   'placeholder': 'Пароль',
                                   'autocomplete': '',
                               }))
    checkbox = forms.BooleanField(initial=False, required=False, widget=forms.CheckboxInput({
        'id': 'rememberId',
        'class': 'custom-control-input'
    }))


class StudentSignUpForm(UserCreationForm):
    group = forms.CharField(required=True)
    specialty = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        Student.objects.create(user=user,
                               group=self.cleaned_data.get('group'),
                               specialty= self.cleaned_data.get('specialty'))
        return user


class TeacherSignUpForm(UserCreationForm):
    degree = forms.CharField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        Teacher.objects.create(user=user,
                               degree=self.cleaned_data.get('degree'))
        return user
