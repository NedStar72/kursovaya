from datetime import datetime

from django.http import Http404
from django.http import HttpRequest
from django.template import RequestContext
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login
from django.urls import reverse

from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
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
            kwargs['teacher'] = self.request.user.teacher
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        if self.request.user.is_teacher:
            teacher = self.request.user.teacher
            context['courseTeacher'] = teacher.teacher_subjects.all()
            context['form'] = forms.TaskAddForm(teacher=teacher)
        if self.request.user.is_student:
            student = self.request.user.student
            courses = student.teacher_subjects.all()
            student_tasks = models.Task.objects.filter(teacher_subjects__in=courses,
                                                       end_date__gte=datetime.now().date()).order_by('end_date').distinct()[:3]
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
    model = models.TeacherSubject
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
        course = self.get_object()
        if self.request.user.is_student and course in request.user.student.teacher_subjects.all():
            return response
        if request.user == course.teacher.user or request.user.is_superuser:
            return response
        return redirect('/')

    def post(self, request, *args, **kwargs):
        if request.user.is_teacher:
            mark = models.Mark.objects.filter(student_teacher_subject__pk=request.POST['student_teacher_subject'],
                                              task__isnull=True).first()
            if mark:
                request.POST = request.POST.copy()
                request.POST['points'] = float(request.POST['points']) + mark.points
                form = forms.MarkAddForm(request.POST, course=self.get_object(), instance=mark)
            else:
                form = forms.MarkAddForm(request.POST, course=self.get_object())
            if form.is_valid():
                form.save()
                return redirect('course', pk=self.get_object().pk)
        return redirect('/')

    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)
        course = context['course']
        context['title'] = "Курс: " + course.subject.name
        context['tasks'] = course.tasks.all()
        s_t_s = models.StudentTeacherSubject.objects.filter(student__in=course.students.all(),
                                                            teacher_subject=course)
        s_marks = [[x.student, x.marks.all()] for x in s_t_s]
        for sm_tuple in s_marks:
            summ = 0
            for mark in sm_tuple[1]:
                summ += mark.points
            sm_tuple[1] = summ
        context['students_marks'] = s_marks
        if self.request.user.is_teacher:
            context['form'] = forms.MarkAddForm(course=course)
        return context


class TaskView(LoginRequiredMixin, DetailView):
    model = models.Task
    template_name = 'task_page.html'
    context_object_name = 'task'

    def get(self, request, *args, **kwargs):
        task = self.get_object()
        if self.request.user.is_student:
            has = False
            courses = task.teacher_subjects.all()
            for course in courses:
                exists = task in course.tasks.all()
                has = has or exists
            if not has:
                return redirect('/')
        if self.request.user.is_teacher and not task.teacher_subjects.filter(teacher=self.request.user.teacher).exists():
                return redirect('/')
        return super(TaskView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.user.is_student:
            if request.POST.__len__() == 1:
                c_t = models.CompletedTask.objects.get(student=request.user.student, task=self.get_object())
                pk = c_t.task.teacher_subjects.filter(students=self.request.user.student).first().pk
                c_t.delete()
                return redirect('course', pk=pk)
            else:
                request.POST = request.POST.copy()
                request.POST['task'] = self.get_object().pk
                try:
                    c_t = models.CompletedTask.objects.get(student=request.user.student, task=self.get_object())
                except Exception:
                    c_t = None
                if c_t:
                    form = forms.CompletedTaskAddForm(request.POST, student=request.user.student, instance=c_t)
                else:
                    form = forms.CompletedTaskAddForm(request.POST, student=request.user.student)
                if form.is_valid():
                    completed_task = form.save()
                    files = request.FILES.getlist('files')
                    if files.__len__() != 0:
                        completed_task.files.all().delete()
                    for file in files:
                        models.TaskFile.objects.create(completed_task=completed_task, file=file)
                    return redirect('task', pk=self.get_object().pk)
        elif request.user.is_teacher:
            if request.POST.__len__() == 1:
                task = self.get_object()
                pk = task.teacher_subjects.first().pk
                task.delete()
                return redirect('course', pk=pk)
            else:
                request.POST = request.POST.copy()
                task = self.get_object()
                request.POST['task'] = task.pk
                mark = models.Mark.objects.filter(student_teacher_subject__pk=request.POST['student_teacher_subject'],
                                                  task=task).first()
                if mark:
                    form = forms.MarkAddForm(request.POST, task=task, instance=mark)
                else:
                    form = forms.MarkAddForm(request.POST, task=task)
                if form.is_valid():
                    form.save()
                    return redirect('task', pk=self.get_object().pk)
        return redirect('/')

    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        task = self.get_object()
        courses = task.teacher_subjects.all()
        context['courses'] = courses
        if self.request.user.is_student:
            student = self.request.user.student
            try:
                context['completed_task'] = task.completed_tasks.get(student=student)
            except models.CompletedTask.DoesNotExist:
                context['completed_task'] = None
            if context['completed_task'] is None:
                if task.end_date >= datetime.now().date() and task.is_reciprocal:
                    context['form'] = forms.CompletedTaskAddForm(student=student)
                else:
                    context['form'] = None
            else:
                context['completed_task_files'] = context['completed_task'].files.all()
                if task.end_date >= datetime.now().date() and task.is_reciprocal:
                    context['form'] = forms.CompletedTaskAddForm(student=student, instance=context['completed_task'])
                else:
                    context['form'] = None
            students_courses = student.teacher_subjects.all()
            context['student_course'] = courses.union(students_courses)
        if self.request.user.is_teacher:
            completed_tasks = list(task.completed_tasks.all())
            marks = list(task.marks.all())
            context['completed_tasks_marks'] = merge_completed_tasks_marks(completed_tasks=completed_tasks, marks=marks)
            context['form'] = forms.MarkAddForm(task=task)
        context['files'] = task.files.all()
        context['title'] = "Задание: " + task.name
        return context


class TaskEditView(LoginRequiredMixin, UpdateView):
    model = models.Task
    form_class = forms.TaskAddForm
    template_name = 'task_edit.html'

    def get_form_kwargs(self):
        kwargs = super(TaskEditView, self).get_form_kwargs()
        if self.request.user.is_teacher:
            kwargs['teacher'] = self.request.user.teacher
        return kwargs

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        task = self.get_object()
        if files.__len__() != 0:
            task.files.all().delete()
            for file in files:
                models.TaskFile.objects.create(task=task, file=file)
        return super(TaskEditView, self).post(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse('task', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super(TaskEditView, self).get_context_data(**kwargs)
        context['title'] = 'Редактировать задание'
        return context


def merge_completed_tasks_marks(completed_tasks, marks):
    list = []
    while completed_tasks or marks:
        completed_task = None
        mark = None
        if completed_tasks:
            completed_task = completed_tasks.pop()
        else:
            mark = marks.pop()
        if completed_task:
            c = None
            for mark in marks:
                if mark.student_teacher_subject.student == completed_task.student:
                    c = mark
                    break
            if not (c is None):
                marks.remove(c)
            list += [(completed_task, c)]
        else:
            c = None
            for completed_task in completed_tasks:
                if mark.student_teacher_subject.student == completed_task.student:
                    c = completed_task
                    break
            if not (c is None):
                completed_tasks.remove(c)
            list += [(c, mark)]
    list.sort(key=sort_merged_list, reverse=True)
    return list


def sort_merged_list(item):
    if item[0] is None:
        return item[1].date
    if item[1] is None:
        return item[0].date
    return item[0].date if item[0].date < item[1].date else item[1].date


class GroupView(LoginRequiredMixin, DetailView):
    model = models.Group
    template_name = 'group_page.html'
    context_object_name = 'group'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_student:
            group = self.get_object()
            student = request.user.student
            if not (student in group.students.all()):
                return redirect('/')
        return super(GroupView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupView, self).get_context_data(**kwargs)
        group = context['group']
        context['students'] = group.students.all()
        context['title'] = "Группа: " + group.name
        return context


class CompletedTaskView(LoginRequiredMixin, DetailView):
    model = models.CompletedTask
    template_name = 'completed_task_page.html'
    context_object_name = 'completed_task'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_teacher and \
                self.get_object().task.teacher_subjects.first().teacher == self.request.user.teacher:
            return super(CompletedTaskView, self).get(request, *args, **kwargs)
        return redirect('/')

    def post(self, request, *args, **kwargs):
        if request.user.is_teacher:
            request.POST = request.POST.copy()
            completed_task = self.get_object()
            task = completed_task.task
            request.POST['task'] = task.pk
            request.POST['student_teacher_subject'] = models.StudentTeacherSubject.objects.filter(
                student=completed_task.student, teacher_subject__in=task.teacher_subjects.all()
            ).first().pk
            mark = completed_task.get_mark()
            if mark:
                form = forms.MarkAddForm(request.POST, task=task, instance=mark)
            else:
                form = forms.MarkAddForm(request.POST, task=task)
            if form.is_valid():
                form.save()
                return redirect('task', pk=self.get_object().task.pk)
        return redirect('/')

    def get_context_data(self, **kwargs):
        context = super(CompletedTaskView, self).get_context_data(**kwargs)
        completed_task = context['completed_task']
        context['form'] = forms.MarkAddForm(task=completed_task.task)
        context['files'] = models.TaskFile.objects.filter(completed_task=completed_task)
        context['title'] = "Ответ: " + completed_task.task.name
        return context
