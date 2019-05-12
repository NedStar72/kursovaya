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
    dayOfWeek = DayOfTheWeekField()
    time = models.TimeField(verbose_name=_(u'Время начала пары'))
    # Надо добавить время начала предмета и время окончания? (что-то вроде продолжительности курса)

    class Meta:
        verbose_name = _(u'Преподаваемый предмет')
        verbose_name_plural = _(u'Преподаваемые предметы')
        ordering = ['subject', 'teacher', 'dayOfWeek']
        db_table = 'Teacher_Subject'

    def get_day(self):
        return DAY_OF_THE_WEEK[self.dayOfWeek]

    def __str__(self):
        return self.subject.__str__() + ' - ' + self.teacher.__str__()


class StudentTeacherSubject(models.Model):
    student = models.ForeignKey(Student, null=True, on_delete=models.SET_NULL)
    teacher_subject = models.ForeignKey(TeacherSubject, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Студент преподаваемого предмета'
        verbose_name_plural = 'Студенты преподаваемых предметов'
        ordering = ['teacher_subject', 'student']
        db_table = 'Student_TeacherSubject'

    def __str__(self):
        return self.student.__str__() + ' ' + self.teacher_subject.__str__()


class Task(models.Model):
    name = models.CharField(max_length=254, verbose_name=_(u'Название'))
    text = models.TextField(verbose_name=_(u'Текст'))
    start_date = models.DateField(verbose_name=_(u'Дата начала'), auto_now=True)
    end_date = models.DateField(verbose_name=_(u'Дата окончания'))
    taught_subjects = models.ManyToManyField(TeacherSubject)

    class Meta:
        verbose_name = _(u'Задание')
        verbose_name_plural = _(u'Задания')
        default_related_name = 'tasks'
        ordering = ['end_date']
        db_table = 'Tasks'

    def __str__(self):
        return self.name.__str__()


class Mark(models.Model):
    student = models.ForeignKey(StudentTeacherSubject, null=True, on_delete=models.SET_NULL)
    task = models.ForeignKey(Task, null=True, on_delete=models.SET_NULL)
    points = models.FloatField(verbose_name='Баллы')
    date = models.DateField(verbose_name='Дата получения')

    class Meta:
        verbose_name = _(u'Оценка')
        verbose_name_plural = _(u'Оценки')
        default_related_name = 'marks'
        ordering = ['date']
        db_table = 'Marks'

    def __str__(self):
        return self.student.__str__() + ' ' + self.points.__str__()


def user_directory_path(instance, filename):
    return 'task_{0}/{1}'.format(instance.task.id, filename)


class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
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
