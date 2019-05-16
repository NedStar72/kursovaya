from datetime import datetime
import os
from django.db import models
from django.db.models.signals import post_delete
from django.utils.translation import ugettext as _
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    patronymic = models.CharField(max_length=63, blank=True, verbose_name='Отчество')
    is_student = models.BooleanField(default=False, verbose_name='Студент')
    is_teacher = models.BooleanField(default=False, verbose_name='Преподаватель')
    # добавить другие поля для инфы?

    def __str__(self):
        return self.last_name.__str__() + ' ' + self.first_name.__str__()


DAY_OF_THE_WEEK = {
        '1': _(u'Monday'),
        '2': _(u'Tuesday'),
        '3': _(u'Wednesday'),
        '4': _(u'Thursday'),
        '5': _(u'Friday'),
        '6': _(u'Saturday'),
    }
TIME = {
    '08:00': '08:00',
    '09:45': '09:45',
    '11:30': '11:30',
    '13:30': '13:30',
}


class DayOfTheWeekField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = tuple(sorted(DAY_OF_THE_WEEK.items()))
        kwargs['max_length'] = 1
        super(DayOfTheWeekField, self).__init__(*args, **kwargs)


class Specialty(models.Model):
    name = models.CharField(max_length=127, verbose_name=_(u'Направление'))

    class Meta:
        verbose_name = _(u'Направление')
        verbose_name_plural = _(u'Направления')
        default_related_name = 'Specialties'
        db_table = 'Specialties'

    def __str__(self):
        return self.name.__str__()


class Group(models.Model):
    name = models.CharField(max_length=127, verbose_name=_(u'Группа'))
    year = models.DateField(verbose_name='Год посутпления')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, verbose_name='Направление')

    class Meta:
        verbose_name = _(u'Группа')
        verbose_name_plural = _(u'Группы')
        default_related_name = 'groups'
        ordering = ['specialty', 'name']
        db_table = 'Groups'

    def __str__(self):
        return self.name.__str__()


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, verbose_name='Группа')

    class Meta:
        verbose_name = _(u'Студент')
        verbose_name_plural = _(u'Студенты')
        ordering = ['user__last_name']
        default_related_name = 'students'
        db_table = 'Students'

    def __str__(self):
        return self.user.last_name.__str__() + ' ' + self.user.first_name.__str__() + ' (' + self.group.name + ')'


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    class Meta:
        verbose_name = _(u'Преподаватель')
        verbose_name_plural = _(u'Преподаватели')
        default_related_name = 'teachers'
        db_table = 'Teachers'

    def __str__(self):
        return self.user.last_name.__str__() + ' ' + self.user.first_name.__str__()


class Subject(models.Model):
    name = models.CharField(max_length=127, verbose_name=_(u'Название'))

    class Meta:
        verbose_name = _(u'Предмет')
        verbose_name_plural = _(u'Предметы')
        default_related_name = 'subjects'
        db_table = 'Subjects'

    def __str__(self):
        return self.name.__str__()


class TeacherSubject(models.Model):
    # Мб subject сделать не отдельной таблицей?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.SET_NULL)
    day_of_week = DayOfTheWeekField()
    time = models.TimeField(verbose_name=_(u'Время начала пары'))
    # Надо добавить время начала предмета и время окончания? (что-то вроде продолжительности курса)

    class Meta:
        verbose_name = _(u'Преподаваемый предмет')
        verbose_name_plural = _(u'Преподаваемые предметы')
        ordering = ['subject', 'teacher', 'day_of_week']
        db_table = 'Teacher_Subject'

    def get_day(self):
        return DAY_OF_THE_WEEK[self.day_of_week]

    def __str__(self):
        return self.subject.__str__() + ' - ' + self.teacher.__str__()


class StudentTeacherSubject(models.Model):
    student = models.ForeignKey(Student, null=True, on_delete=models.SET_NULL)
    teacher_subject = models.ForeignKey(TeacherSubject, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Студент преподаваемого предмета'
        verbose_name_plural = 'Студенты преподаваемых предметов'
        ordering = ['student__user__last_name', 'student__pk']
        db_table = 'Student_TeacherSubject'

    def __str__(self):
        return self.student.__str__()  # + ' ' + self.teacher_subject.__str__()


class Task(models.Model):
    name = models.CharField(max_length=254, verbose_name=_(u'Название'))
    text = models.TextField(verbose_name=_(u'Текст'))
    start_date = models.DateField(verbose_name=_(u'Дата начала'), auto_now=True)
    end_date = models.DateField(verbose_name=_(u'Дата окончания'))
    teacher_subjects = models.ManyToManyField(TeacherSubject)

    class Meta:
        verbose_name = _(u'Задание')
        verbose_name_plural = _(u'Задания')
        default_related_name = 'tasks'
        ordering = ['end_date']
        db_table = 'Tasks'

    def __str__(self):
        return self.name.__str__()


class CompletedTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    text = models.TextField(verbose_name=_(u'Текст'))
    date = models.DateField(verbose_name=_(u'Дата'), auto_now=True)

    class Meta:
        verbose_name = _(u'Выполненное задание')
        verbose_name_plural = _(u'Выполненные задания')
        default_related_name = 'completed_tasks'
        ordering = ['date', 'task__name', 'student__user__last_name']
        db_table = 'CompletedTasks'

    def __str__(self):
        return self.task.__str__() + ' - ' + self.student.__str__()


def user_directory_path(instance, filename):
    if instance.task:
        return 'task_{0}/{1}'.format(instance.task.id, filename)
    else:
        return 'student_{0}/{1}/{2}'.format(instance.completed_task.student.user.id, datetime.now().year, filename)


class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True)
    completed_task = models.ForeignKey(CompletedTask, on_delete=models.CASCADE, null=True)
    file = models.FileField(upload_to=user_directory_path)

    class Meta:
        verbose_name = 'Прикрепленный к заданию файл'
        verbose_name_plural = 'Прикрепленные к заданиям файлы'
        ordering = ['task']
        db_table = 'TaskFiles'

    def css_class(self):
        name, extension = os.path.splitext(self.file.name)
        if extension == '.pdf':
            return 'pdf'
        if extension == '.doc' or extension == '.docx':
            return 'word'
        if extension == '.ppt' or extension == '.pptx':
            return 'pp'
        if extension == '.jpg' or extension == '.png':
            return 'photo'
        if extension == '.xls' or extension == '.xlsx':
            return 'exel'
        if extension == '.txt':
            return 'text'
        return 'other'

    def __str__(self):
        return self.file.__str__().split('/')[-1]


class Mark(models.Model):
    completed_task = models.ForeignKey(CompletedTask, on_delete=models.CASCADE)
    points = models.FloatField(verbose_name='Баллы')
    date = models.DateField(verbose_name='Дата получения', auto_now=True)

    class Meta:
        verbose_name = _(u'Оценка')
        verbose_name_plural = _(u'Оценки')
        default_related_name = 'marks'
        ordering = ['date', 'completed_task__task__name', 'completed_task__student__last_name']
        db_table = 'Marks'

    def __str__(self):
        return self.completed_task.__str__() + ' : ' + self.points.__str__()
