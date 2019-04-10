from django.contrib import admin
from django.urls import path, include
from datetime import datetime

from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
import app.view as view
import app.forms

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/',
         LoginView.as_view(authentication_form=app.forms.AuthForm, redirect_authenticated_user=True, extra_context={
             'title': 'Страница входа',
             'year': datetime.now().year
         })
         , name="login"),
    path('logout/',
         LogoutView.as_view(), name='logout'),
    path('', view.home, name='home'),
]
