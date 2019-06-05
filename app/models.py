from datetime import datetime
from datetime import timedelta
import os
from django.db import models
from django.db.models.signals import post_delete
from django.utils.translation import ugettext as _
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, m2m_changed
from notifications.signals import notify
from notifications.models import Notification
from django.dispatch import receiver


def user_avatar_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.id, filename)


class User(AbstractUser):
    patronymic = models.CharField(max_length=63, blank=True, verbose_name='Отчество')
    is_student = models.BooleanField(default=False, verbose_name='Студент')
    is_teacher = models.BooleanField(default=False, verbose_name='Преподаватель')
    avatar = models.ImageField(upload_to=user_avatar_path, null=True, default='/default-avatar.png',
                               verbose_name='Аватар')
    # добавить другие поля для инфы?

    def __str__(self):
        if self.patronymic:
            return self.last_name.__str__() + ' ' + self.first_name.__str__() + ' ' + self.patronymic.__str__()
        else:
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
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, verbose_name='Направление',
                                  related_name='groups', related_query_name='groups')

    class Meta:
        verbose_name = _(u'Группа')
        verbose_name_plural = _(u'Группы')
        default_related_name = 'groups'
        ordering = ['specialty', 'name']
        db_table = 'Groups'

    def __str__(self):
        return self.name.__str__()


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, verbose_name='Группа',
                              related_name='students', related_query_name='students')

    class Meta:
        verbose_name = _(u'Студент')
        verbose_name_plural = _(u'Студенты')
        ordering = ['user__last_name']
        default_related_name = 'students'
        db_table = 'Students'

    def get_marks(self):
        return Mark.objects.filter(student_teacher_subject__in=StudentTeacherSubject.objects.filter(student=self))

    def __str__(self):
        return self.user.last_name.__str__() + ' ' + self.user.first_name.__str__() + ' (' + self.group.name + ')'


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='teacher')

    class Meta:
        verbose_name = _(u'Преподаватель')
        verbose_name_plural = _(u'Преподаватели')
        default_related_name = 'teachers'
        db_table = 'Teachers'

    def __str__(self):
        return self.user.last_name.__str__() + ' ' + self.user.first_name.__str__() + ' ' + self.user.patronymic.__str__()


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
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_subjects',
                                related_query_name='teacher_subjects')
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.SET_NULL, related_name='teacher_subjects',
                                related_query_name='teacher_subjects')
    day_of_week = DayOfTheWeekField()
    time = models.TimeField(verbose_name=_(u'Время начала пары'))
    students = models.ManyToManyField(Student, related_name='teacher_subjects', related_query_name='teacher_subjects',
                                      through='StudentTeacherSubject')
    # Надо добавить время начала предмета и время окончания? (что-то вроде продолжительности курса)

    class Meta:
        verbose_name = _(u'Преподаваемый предмет')
        verbose_name_plural = _(u'Преподаваемые предметы')
        ordering = ['day_of_week', 'time', 'subject__name', 'teacher']
        db_table = 'Teacher_Subject'

    def get_day(self):
        return DAY_OF_THE_WEEK[self.day_of_week]

    def get_marks(self, student):
        return Mark.objects.filter(
            student_teacher_subject=StudentTeacherSubject.objects.get(student=student, teacher_subject=self)
        )

    def get_end_time(self):
        start = datetime(
            2000, 1, 1,
            hour=self.time.hour, minute=self.time.minute, second=self.time.second)
        end = start + timedelta(hours=1, minutes=30)
        return end.time()

    def str_for_n(self):
        return self.__str__()

    def __str__(self):
        return self.subject.__str__()


class StudentTeacherSubject(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher_subject = models.ForeignKey(TeacherSubject, on_delete=models.CASCADE)

    def __str__(self):
        return self.student.__str__()


class Task(models.Model):
    name = models.CharField(max_length=254, verbose_name=_(u'Название'))
    text = models.TextField(verbose_name=_(u'Текст'))
    start_date = models.DateField(verbose_name=_(u'Дата начала'), auto_now_add=True)
    end_date = models.DateField(verbose_name=_(u'Дата окончания'))
    teacher_subjects = models.ManyToManyField(TeacherSubject, related_name='tasks', related_query_name='tasks',
                                              verbose_name='Курсы')
    is_reciprocal = models.BooleanField(default=False, verbose_name='Разрешить ответы')
    is_created = models.BooleanField(default=True)

    class Meta:
        verbose_name = _(u'Задание')
        verbose_name_plural = _(u'Задания')
        default_related_name = 'tasks'
        ordering = ['end_date', 'start_date', 'name']
        db_table = 'Tasks'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, is_notification=True):
        super(Task, self).save(force_insert=force_insert, force_update=force_update, using=using,
                               update_fields=update_fields)
        if is_notification:
            notify.send(sender=self,
                        recipient=User.objects.filter(student__in=Student.objects.filter(
                            teacher_subjects__in=self.teacher_subjects.all())),
                        verb='Обновлено задание.',
                        description='task')

    def delete(self, using=None, keep_parents=False):
        TaskFile.objects.filter(task=self).delete()
        Notification.objects.filter(actor_object_id=self.id).delete()
        super(Task, self).delete(using, keep_parents)

    def get_teacher(self):
        return self.teacher_subjects.first().teacher

    def get_course(self, student):
        return self.teacher_subjects.intersection(student.teacher_subjects.all())

    def str_for_n(self):
        return self.name

    def __str__(self):
        return self.name.__str__()


class CompletedTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completed_tasks',
                             related_query_name='completed_tasks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    text = models.TextField(verbose_name=_(u'Текст'))
    date = models.DateField(verbose_name=_(u'Дата'), auto_now=True)

    class Meta:
        verbose_name = _(u'Выполненное задание')
        verbose_name_plural = _(u'Выполненные задания')
        default_related_name = 'completed_tasks'
        ordering = ['date', 'task__name', 'student__user__last_name']
        db_table = 'CompletedTasks'

    def get_mark(self):
        try:
            return Mark.objects.get(
                task=self.task,
                student_teacher_subject=StudentTeacherSubject.objects.filter(
                    student=self.student,
                    teacher_subject__in=self.task.teacher_subjects.all()
                ).first()
            )
        except:
            return None

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(CompletedTask, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                        update_fields=update_fields)
        notify.send(sender=self,
                    recipient=self.task.get_teacher().user,
                    verb='Получен ответ.',
                    description='completed_task')

    def str_for_n(self):
        return self.task.str_for_n()

    def delete(self, using=None, keep_parents=False):
        files = TaskFile.objects.filter(completed_task=self)
        for file in files:
            file.delete()
        Notification.objects.filter(actor_object_id=self.id).delete()
        # mark = self.get_mark()
        # if mark:
        #     mark.delete()
        super(CompletedTask, self).delete(using, keep_parents)

    def __str__(self):
        return self.task.__str__() + ' - ' + self.student.__str__()


def user_directory_path(instance, filename):
    if instance.task:
        return 'task_{0}/{1}'.format(instance.task.id, filename)
    else:
        return 'student_{0}/{1}/{2}'.format(instance.completed_task.student.user.id, datetime.now().year, filename)


class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, related_name='files',
                             related_query_name='files')
    completed_task = models.ForeignKey(CompletedTask, on_delete=models.CASCADE, null=True,
                                       related_name='files', related_query_name='files')
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
            return 'excel'
        if extension == '.txt':
            return 'text'
        return 'other'

    def __str__(self):
        return self.file.__str__().split('/')[-1]


class Mark(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='marks', related_query_name='marks',
                             null=True)
    student_teacher_subject = models.ForeignKey(StudentTeacherSubject, on_delete=models.CASCADE,
                                                related_name='marks',
                                                related_query_name='marks')
    points = models.FloatField(verbose_name='Баллы')
    date = models.DateField(verbose_name='Дата получения', auto_now_add=True)

    class Meta:
        verbose_name = _(u'Оценка')
        verbose_name_plural = _(u'Оценки')
        default_related_name = 'marks'
        ordering = ['date']
        db_table = 'Marks'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(Mark, self).save(force_insert=force_insert, force_update=force_update, using=using,
                               update_fields=update_fields)
        if self.task is None:
            notify.send(sender=self.student_teacher_subject.teacher_subject,
                        recipient=self.student_teacher_subject.student.user,
                        verb='Выставлены баллы',
                        description='course')
        else:
            notify.send(sender=self.task,
                        recipient=self.student_teacher_subject.student.user,
                        verb='Выставлены баллы',
                        description='task')

    def get_completed_task(self):
        try:
            return CompletedTask.objects.get(
                task=self.task, student=self.student_teacher_subject.student
            )
        except:
            return None

    def str_for_n(self):
        return self.task.str_for_n()

    @staticmethod
    def sum(marks):
        summa = 0
        for mark in marks:
            summa += mark.points
        count = marks.count()
        if count == 0:
            return 0
        else:
            return summa

    def __str__(self):
        return self.task.__str__() + ' : ' + self.points.__str__()


@receiver(m2m_changed, sender=TeacherSubject.tasks.through)
def task_created(sender, instance, **kwargs):
    if kwargs['action'] == "post_add" and instance.is_created:
        notify.send(sender=instance,
                    recipient=User.objects.filter(student__in=Student.objects.filter(
                        teacher_subjects__in=instance.teacher_subjects.all())),
                    verb='Новое задание.')
        instance.is_created = False
        instance.save(is_notification=False)
