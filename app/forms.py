from django import forms
from django.contrib.auth.forms import AuthenticationForm


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
    checkbox = forms.BooleanField(initial=True, required=False, widget=forms.CheckboxInput({
        'id': 'rememberId',
        'class': 'custom-control-input'
    }))

