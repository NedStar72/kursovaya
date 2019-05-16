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
            student = models.Student.objects.get(user=self.request.user)
            courses = [x.teacher_subject for x in models.StudentTeacherSubject.objects.filter(student=student)]
            student_tasks = models.Task.objects.filter(teacher_subjects__in=courses,
                                                       end_date__gte=datetime.now().date()).order_by('end_date')[:3]
            temp = []
            for task in student_tasks:
                for course in courses:
                    if course in task.teacher_subjects.all():
                        temp += [(task, course)]
                        break
            context['student_tasks'] = temp
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
        context['title'] = "Курс: " + self.object.subject.name
        context['students'] = [x.student for x in models.StudentTeacherSubject.objects.filter(
            teacher_subject=self.object)]
        context['tasks'] = models.Task.objects.filter(teacher_subjects=self.get_object())
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
            t_subjects = task.teacher_subjects.all()
            for t_subject in t_subjects:
                exists = models.StudentTeacherSubject.objects.filter(teacher_subject=t_subject,
                                                                     student=student).exists()
                has = has or exists
            if not has:
                return redirect('/')
        if self.request.user.is_teacher and task.teacher_subjects.first().teacher != models.Teacher.objects.get(
                user=request.user):
                return redirect('/')
        return super(TaskView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.user.is_student:
            request.POST = request.POST.copy()
            request.POST['task'] = self.get_object().pk
            c_t = models.CompletedTask.objects.get(student=models.Student.objects.get(user=request.user),
                                                   task=self.get_object())
            if c_t:
                form = forms.CompletedTaskAddForm(request.POST, student=models.Student.objects.get(user=request.user),
                                                  instance=c_t)
            else:
                form = forms.CompletedTaskAddForm(request.POST, student=models.Student.objects.get(user=request.user))
            if form.is_valid():
                completed_task = form.save()
                files = request.FILES.getlist('files')
                if files.__len__ != 0:
                    models.TaskFile.objects.filter(completed_task=completed_task).delete()
                for file in files:
                    models.TaskFile.objects.create(completed_task=completed_task, file=file)
                return redirect('task', pk=self.get_object().pk)
        elif request.user.is_teacher:
            abs = 123
            # form = forms.MarkAddForm(request.POST, task=self.get_object())
            # if form.is_valid():
            #     form.save()
            #     return redirect('task', pk=self.get_object().pk)
        return redirect('/')

    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        task = self.get_object()
        if self.request.user.is_student:
            student = models.Student.objects.get(user=self.request.user)
            try:
                context['completed_task'] = models.CompletedTask.objects.get(student=student, task=self.get_object())
            except models.CompletedTask.DoesNotExist:
                context['completed_task'] = None
            if context['completed_task'] is None:
                context['form'] = forms.CompletedTaskAddForm(student=student)
            else:
                context['completed_task_files'] = models.TaskFile.objects.filter(completed_task=context['completed_task'])
                if context['completed_task'].task.end_date > datetime.now().date():
                    context['form'] = forms.CompletedTaskAddForm(student=student, instance=context['completed_task'])
                else:
                    context['form'] = None
        # context['form'] = forms.MarkAddForm(task=task)
        # context['marks'] = models.Mark.objects.filter(task=task)
        context['files'] = models.TaskFile.objects.filter(task=task)
        context['title'] = "Задание: " + task.name
        return context


class GroupView(LoginRequiredMixin, DetailView):
    model = models.Group
    template_name = 'group_page.html'
    context_object_name = 'group'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_student:
            group = self.get_object()
            student = models.Student.objects.get(user=request.user)
            if not (student in models.Student.objects.filter(group=group)):
                return redirect('/')
        return super(GroupView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupView, self).get_context_data(**kwargs)
        context['students'] = [x for x in models.Student.objects.filter(group=self.object)]
        context['title'] = "Группа: " + self.object.name
        return context
