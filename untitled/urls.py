from django.contrib import admin
from django.urls import path, include
from datetime import datetime

from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
import app.view as view
import app.forms

urlpatterns = [
    path('admin/', admin.site.urls),
    path('registration/', app.view.RegisterFormView.as_view()),
    path('login/', view.MyLoginView.as_view(),  name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', view.home, name='home'),
]
