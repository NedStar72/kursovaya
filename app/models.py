from datetime import datetime
from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    patronymic = models.CharField(max_length=63, blank=True)
    is_student = models.BooleanField('student status', default=False)
    is_teacher = models.BooleanField('teacher status', default=False)
    # добавить другие поля для инфы?


DAY_OF_THE_WEEK = {
        '1': _(u'Monday'),
        '2': _(u'Tuesday'),
        '3': _(u'Wednesday'),
        '4': _(u'Thursday'),
        '5': _(u'Friday'),
        '6': _(u'Saturday'),
        '7': _(u'Sunday'),
    }


class DayOfTheWeekField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = tuple(sorted(DAY_OF_THE_WEEK.items()))
        kwargs['max_length'] = 1
        super(DayOfTheWeekField, self).__init__(*args, **kwargs)

    class Meta:
        verbose_name = _(u'День недели')


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    group = models.CharField(max_length=127, verbose_name=_(u'Группа'))
    specialty = models.CharField(max_length=127, verbose_name=_(u'Напревление'))

    class Meta:
        verbose_name = _(u'Студент')
        default_related_name = _(u'Студенты')
        ordering = ['specialty', 'group']
        db_table = 'Students'


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    degree = models.CharField(max_length=127, verbose_name=_(u'Степень'))

    class Meta:
        verbose_name = _(u'Преподаватель')
        default_related_name = _(u'Преподаватели')
        db_table = 'Teachers'


class Subject(models.Model):
    name = models.CharField(max_length=127, verbose_name=_(u'Название'))

    class Meta:
        verbose_name = _(u'Предмет')
        default_related_name = _(u'Предметы')
        db_table = 'Subjects'


class TeacherSubject(models.Model):
    # Мб subject сделать не отдельной таблицей?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    dayOfWeek = DayOfTheWeekField()
    time = models.TimeField(verbose_name=_(u'Время начала пары'))
    # Надо добавить время начала предмета и время окончания? (что-то вроде продолжительности курса)

    class Meta:
        verbose_name = _(u'Преподаваемый_предмет')
        default_related_name = _(u'Преподаваемые_предметы')
        ordering = ['subject', 'teacher', 'dayOfWeek']
        db_table = 'Teacher_Subject'


class StudentTeacherSubject(models.Model):
    student = models.ForeignKey(Student, null=True, on_delete=models.SET_NULL)
    teacher_subject = models.ForeignKey(TeacherSubject, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _(u'Студент_преподаваемого_предмета')
        default_related_name = _(u'Студенты_преподаваемого_предмета')
        ordering = ['teacher_subject', 'student']
        db_table = 'Student_TeacherSubject'


class Task(models.Model):
    name = models.CharField(max_length=254, verbose_name=_(u'Название'))
    text = models.TextField(verbose_name=_(u'Текст'))
    start_date = models.DateTimeField(verbose_name=_(u'Дата начала'))
    end_date = models.DateTimeField(verbose_name=_(u'Дата окончания'))
    taught_subject = models.ForeignKey(TeacherSubject, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _(u'Задание')
        default_related_name = _(u'Задания')
        ordering = ['taught_subject', 'start_date']
        db_table = 'Tasks'


class Mark(models.Model):
    student = models.ForeignKey(StudentTeacherSubject, null=True, on_delete=models.SET_NULL)
    task = models.ForeignKey(Task, null=True, on_delete=models.SET_NULL)
    points = models.FloatField(verbose_name='Баллы')
    date = models.DateField(verbose_name='Дата получения')

    class Meta:
        verbose_name = _(u'Оценка')
        default_related_name = _(u'Оценки')
        ordering = ['date']
        db_table = 'Marks'


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}/{2}'.format(instance.user.id, datetime.now().year, filename)


class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)

    class Meta:
        verbose_name = _(u'Прикрепленный_к_заданию_файл')
        default_related_name = _(u'Прикрепленный_к_заданию_файлы')
        ordering = ['task']
        db_table = 'TaskFiles'
