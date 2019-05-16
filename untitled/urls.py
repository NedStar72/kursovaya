from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
import app.view as view
import app.forms

urlpatterns = [
    path('admin/', admin.site.urls, name='adminPanel'),
    path('registration/student/', app.view.StudentRegisterFormView.as_view(), name='student_registration'),
    path('registration/teacher/', app.view.TeacherRegisterFormView.as_view(), name='teacher_registration'),
    path('registration/', app.view.RegisterView.as_view(), name='registration'),
    path('login/', view.MyLoginView.as_view(),  name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('subject/add/', view.SubjectAddFormView.as_view(), name='add_subject'),
    path('speciality/add/', view.SpecialityAddFormView.as_view(), name='add_speciality'),
    path('group/add/', view.GroupAddFormView.as_view(), name='add_group'),
    path('group/<int:pk>/', view.GroupView.as_view(), name='group'),
    path('course/add/', view.CourseAddFormView.as_view(), name='add_course'),
    path('course/<int:pk>/', view.CourseView.as_view(), name='course'),
    path('task/<int:pk>/', view.TaskView.as_view(), name='task'),
    path('', view.HomeView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
