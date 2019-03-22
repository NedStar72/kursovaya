from django.shortcuts import render
from django.http import HttpRequest
from django.template import RequestContext
from datetime import  datetime

def home(request):
    assert isinstance(request, HttpRequest) #проверка исходных данных
    return render(
        request,
        'home.html',
        {
            'title':'Домашнаяя страница',
            'year':datetime.now().year
        }
    )