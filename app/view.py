from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpRequest
from django.http import Http404
from django.shortcuts import render
from datetime import datetime
import app.forms


@login_required
def home(request):
    assert isinstance(request, HttpRequest)  # проверка исходных данных
    return render(
        request,
        'home.html',
        {
            'title': 'Главная страница',
            'year': datetime.now().year
        }
    )


from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm


class RegisterFormView(FormView):
    form_class = UserCreationForm

    # Ссылка, на которую будет перенаправляться пользователь в случае успешной регистрации.
    # В данном случае указана ссылка на страницу входа для зарегистрированных пользователей.
    success_url = "/login/"

    # Шаблон, который будет использоваться при отображении представления.
    template_name = "registration/registration.html"

    def form_valid(self, form):
        # Создаём пользователя, если данные в форму были введены корректно.
        form.save()

        # Вызываем метод базового класса
        return super(RegisterFormView, self).form_valid(form)


from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.http import HttpResponseRedirect


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
