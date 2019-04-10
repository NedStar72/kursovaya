from django.shortcuts import render
from django.http import HttpRequest
from django.template import RequestContext
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import Http404


@login_required
def home(request):
    assert isinstance(request, HttpRequest)  # проверка исходных данных
    return render(
        request,
        'home.html',
        {
            'title': 'Домашнаяя страница',
            'year': datetime.now().year
        }
    )
