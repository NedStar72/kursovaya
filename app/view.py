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
from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView

from django.contrib.auth.forms import UserCreationForm
import app.models as models
import app.forms as forms

from braces import views


class HomeView(LoginRequiredMixin, CreateView):
    form_class = forms.TaskAddForm
    template_name = 'home.html'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            task = form.save()
            for file in request.FILES.getlist('files'):
                models.TaskFile.objects.create(task=task, file=file)
            return redirect('/task/' + task.pk.__str__())  # удачно
        return redirect('/')  # неудачно

    def get_form_kwargs(self):
        kwargs = super(HomeView, self).get_form_kwargs()
        if self.request.user.is_teacher:
            kwargs['teacher'] = models.Teacher.objects.get(user=self.request.user)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        if self.request.user.is_teacher:
            teacher = models.Teacher.objects.get(user=self.request.user)
            context['courseTeacher'] = models.TeacherSubject.objects.filter(teacher=teacher)
            context['form'] = forms.TaskAddForm(teacher=teacher)
        if self.request.user.is_student:
            context['courseStudent'] = 0  # изменить
        context['title'] = 'Главная страница'
        context['year'] = datetime.now().year
        return context


class SubjectAddFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "subject_add.html"
    model = models.Subject
    form_class = forms.SubjectAddForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Добавить предмет'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('/')


class SpecialityAddFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "subject_add.html"
    model = models.Specialty
    form_class = forms.SpecialtyAddForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Добавить направление'
        return super().get_context_data(**kwargs)


class GroupAddFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "group_add.html"
    model = models.Group
    form_class = forms.GroupAddForm

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
    model = models.User
    form_class = forms.StudentSignUpForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Регистрация студента'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('/admin')


class TeacherRegisterFormView(LoginRequiredMixin, views.SuperuserRequiredMixin, CreateView):
    success_url = "/"
    template_name = "registration/t_registration.html"
    model = models.User
    form_class = forms.TeacherSignUpForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Регистрация преподавателя'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('/admin')


class MyLoginView(LoginView):
    authentication_form = forms.AuthForm
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
    template_name = "course_add.html"
    model = models.StudentTeacherSubject
    form_class = forms.CourseAddForm

    def get_context_data(self, **kwargs):
        kwargs['title'] = 'Добавить курс'
        return super().get_context_data(**kwargs)


class CourseView(LoginRequiredMixin, DetailView):
    model = models.TeacherSubject
    template_name = 'course_page.html'
    context_object_name = 'course'

    def get(self, request, *args, **kwargs):
        response = super(CourseView, self).get(request, *args, **kwargs)
        if self.request.user.is_student and \
                models.StudentTeacherSubject.objects.filter(
                    teacher_subject=self.object,
                    student=models.Student.objects.get(user=self.request.user)).exists():
            return response
        if request.user == self.object.teacher.user or request.user.is_superuser:
            return response
        return redirect('/')

    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)
        context['title'] = "Группа: " + self.object.subject.name
        context['students'] = [x.student for x in models.StudentTeacherSubject.objects.filter(teacher_subject=self.object)]
        context['tasks'] = models.Task.objects.filter(taught_subjects=self.object)
        return context


# изменить порядок в get используя get_object
class TaskView(LoginRequiredMixin, DetailView):
    model = models.Task
    template_name = 'task_page.html'
    context_object_name = 'task'

    def get(self, request, *args, **kwargs):
        task = self.get_object()
        if self.request.user.is_student:
            has = False
            student = models.Student.objects.get(user=request.user)
            t_subjects = task.taught_subjects.all()
            for t_subject in t_subjects:
                exists = models.StudentTeacherSubject.objects.filter(teacher_subject=t_subject, student=student).exists()
                has = has or exists
            if not has:
                return redirect('/')
        if self.request.user.is_teacher and task.taught_subjects.first().teacher != models.Teacher.objects.get(user=request.user):
                return redirect('/')
        return super(TaskView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        context['files'] = models.TaskFile.objects.filter(task=self.object)
        context['title'] = "Задание: " + self.object.name
        return context
