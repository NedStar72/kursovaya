import datetime
import operator
from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm as _UserCreationForm
from django.db import transaction
from django.core.files.images import get_image_dimensions
from django.contrib.auth.forms import PasswordChangeForm
import app.models as models


class AuthForm(AuthenticationForm):
    username = forms.CharField(required=True, max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control form-control-lg mb-4',
                                   'placeholder': 'Логин',
                                   'autocomplete': '',
                               }))
    password = forms.CharField(required=True, max_length=254,
                               widget=forms.PasswordInput({
                                   'class': 'form-control form-control-lg mb-4',
                                   'placeholder': 'Пароль',
                                   'autocomplete': '',
                               }))
    checkbox = forms.BooleanField(initial=False, required=False, widget=forms.CheckboxInput({
        'id': 'rememberId',
        'class': 'custom-control-input'
    }))


class UserCreationForm(_UserCreationForm):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(UserCreationForm, self).__init__(*args, **kwargs)

    f_name = forms.CharField(max_length=256, required=True, label='Имя', widget=forms.TextInput(attrs={
        'class': 'form-control mb-3',
        'placeholder': 'Введите имя',
    }))
    s_name = forms.CharField(max_length=256, required=True, label='Фамилия', widget=forms.TextInput(attrs={
        'class': 'form-control mb-3',
        'placeholder': 'Введите фамилию',
    }))
    t_name = forms.CharField(max_length=256, required=False, label='Отчество', widget=forms.TextInput(attrs={
        'class': 'form-control mb-3',
        'placeholder': 'Введите отчество',
    }))
    email = forms.EmailField(required=False, label='Почта', widget=forms.TextInput(attrs={
        'class': 'form-control mb-3',
        'placeholder': 'Введите почту',
    }))

    class Meta(_UserCreationForm.Meta):
        model = models.User

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit)
        user.first_name = self.cleaned_data["f_name"]
        user.last_name = self.cleaned_data["s_name"]
        user.patronymic = self.cleaned_data["t_name"]
        user.email = self.cleaned_data["email"]
        user.save(commit)
        return user


class StudentSignUpForm(UserCreationForm):

    group = forms.ChoiceField(required=True, choices=[], label='Группа')

    def __init__(self, *args, **kwargs):
        super(StudentSignUpForm, self).__init__(*args, **kwargs)
        self.fields['group'].choices = [(x.pk, x.name) for x in models.Group.objects.all()]
        self.fields['username'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        self.fields['group'].widget.attrs['class'] = 'mdb-select'
        self.fields['group'].widget.attrs['searchable'] = 'Поиск...'

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        models.Student.objects.create(user=user,
                                      group=models.Group.objects.get(pk=int(self.cleaned_data["group"])))
        return user


class TeacherSignUpForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(TeacherSignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control mb-3'

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True
        user.save()
        models.Teacher.objects.create(user=user)
        return user


class MyPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control mb-3'


class SubjectAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SubjectAddForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control mb-0'

    class Meta:
        model = models.Subject
        fields = ['name']
        labels = {
            'name': 'Название предмета',
        }


class SpecialtyAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(SpecialtyAddForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.Specialty
        fields = ['name']
        labels = {
            'name': 'Название направления',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control mb-0',
            }),
        }


class GroupAddForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(GroupAddForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.Group
        fields = ['name', 'year', 'specialty']
        labels = {
            'name': 'Название группы',
            'year': 'Год поступления',
            'specialty': 'Направление',
        }
        years = {}
        for x in range(2015, datetime.datetime.now().year):
            years[datetime.datetime(year=x, month=1, day=1).date()] = x.__str__()
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'year': forms.Select(attrs={
                'class': 'mdb-select',
            },
                choices=years.items()),
            'specialty': forms.Select(attrs={
                'class': 'mdb-select',
                'searchable': 'Пойск...',
            }),
        }

    def clean(self):
        return super(GroupAddForm, self).clean()


class CourseAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(CourseAddForm, self).__init__(*args, **kwargs)

    subject = forms.ModelChoiceField(required=True,
                                     queryset=models.Subject.objects.all(),
                                     label='Предмет',
                                     empty_label='Выберите предмет',
                                     widget=forms.Select(attrs={
                                         'class': 'mdb-select',
                                         'searchable': 'Пойск',
                                     }))
    day_of_week = forms.ChoiceField(required=True,
                                    choices=models.DAY_OF_THE_WEEK.items(),
                                    label='День недели',
                                    widget=forms.Select(attrs={
                                        'class': 'mdb-select',
                                    }))
    time = forms.ChoiceField(required=True,
                             choices=models.TIME.items(),
                             label='Время пары',
                             widget=forms.Select(attrs={
                                 'class': 'mdb-select',
                             }))
    teacher = forms.ModelChoiceField(required=True,
                                     queryset=models.Teacher.objects.all(),
                                     label='Преподаватель',
                                     empty_label='Выберите преподавателя',
                                     widget=forms.Select(attrs={
                                         'class': 'mdb-select',
                                         'searchable': 'Пойск',
                                     }))
    students = forms.MultipleChoiceField(choices=[(x.user.pk, x.user.last_name + ' ' + x.user.first_name + ' '
                                                   + x.user.patronymic) for x in models.Student.objects.all()],
                                         label='Студенты',
                                         required=True,
                                         widget=forms.SelectMultiple(attrs={
                                             'class': 'mdb-select',
                                             'multiple': '',
                                             'searchable': 'Пойск',
                                         }))

    class Meta:
        model = models.TeacherSubject
        fields = ['subject', 'day_of_week', 'time', 'teacher', 'students']

    @transaction.atomic
    def save(self, commit=True):
        course = models.TeacherSubject.objects.create(teacher=self.cleaned_data.get('teacher'),
                                                      subject=self.cleaned_data.get('subject'),
                                                      day_of_week=self.cleaned_data.get('day_of_week'),
                                                      time=datetime.datetime.strptime(self.cleaned_data.get('time'),
                                                                                      '%H:%M').time())
        students = models.Student.objects.filter(user_id__in=self.cleaned_data.get('students'))
        models.StudentTeacherSubject.objects.bulk_create(
            [models.StudentTeacherSubject(student=s, teacher_subject=course) for s in students]
        )
        return course


class TaskAddForm(forms.ModelForm):
    name = forms.CharField(max_length=254, label='Название',
                           widget=forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': 'Введите название',
                           }))

    end_date = forms.DateField(label='Дата окончания', input_formats=['%d/%m/%Y', '%d.%m.%Y'],
                               widget=forms.DateInput(attrs={
                                   'class': 'form-control datepicker',
                                   'placeholder': 'Выберите дату',
                               }))

    files = forms.FileField(label='Выберите файлы', required=False,
                            widget=forms.ClearableFileInput(attrs={
                                'multiple': True,
                            }))

    is_reciprocal = forms.BooleanField(initial=True, required=False,
                                       label='Разрешить ответы',
                                       widget=forms.CheckboxInput({
                                           'class': 'custom-control-input'
                                       }))

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        teacher = kwargs.pop('teacher', None)
        if teacher:
            super(TaskAddForm, self).__init__(*args, **kwargs)
            self.fields['teacher_subjects'] = forms.MultipleChoiceField(
                choices=[(x.pk, x.subject.__str__() + ' (' + x.get_day() + ', ' + x.time.strftime('%H:%M') + ')')
                         for x in teacher.teacher_subjects.all()],
                widget=forms.SelectMultiple(attrs={
                    'placeholder': 'Выберите предметы',
                    'multiple': '',
                    'class': 'mdb-select',
                    'searchable': 'Пойск',
                }),
                label='Курсы')
            self.fields['text'].required = False

    class Meta:
        model = models.Task
        fields = ['name', 'teacher_subjects', 'end_date', 'text', 'is_reciprocal', 'files']
        labels = {
            'text': 'Текст',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
            }),
        }


class TaskEditForm(forms.ModelForm):
    name = forms.CharField(max_length=254, label='Название',
                           widget=forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': 'Введите название',
                           }))

    end_date = forms.DateField(label='Дата окончания', input_formats=['%d/%m/%Y', '%d.%m.%Y'],
                               widget=forms.DateInput(attrs={
                                   'class': 'form-control datepicker',
                                   'placeholder': 'Выберите дату',
                               }))

    files = forms.FileField(label='Выберите файлы', required=False,
                            widget=forms.ClearableFileInput(attrs={
                                'multiple': True,
                            }))

    is_reciprocal = forms.BooleanField(initial=True, required=False,
                                       label='Разрешить ответы',
                                       widget=forms.CheckboxInput({
                                           'class': 'custom-control-input'
                                       }))

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(TaskEditForm, self).__init__(*args, **kwargs)
        self.fields['text'].required = False

    class Meta:
        model = models.Task
        fields = ['name', 'end_date', 'text', 'is_reciprocal', 'files']
        labels = {
            'text': 'Текст',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
            }),
        }


class CompletedTaskAddForm(forms.ModelForm):

    task = forms.ModelChoiceField(required=True,
                                  label='Студент',
                                  queryset=models.Task.objects.none(),
                                  widget=forms.Select(attrs={
                                      'class': 'mdb-select',
                                      'searchable': 'Пойск',
                                  }))
    text = forms.CharField(required=False, label='Текст',
                           widget=forms.Textarea(attrs={
                               'class': 'form-control',
                               'rows': '3',
                               'placeholder': 'Написать текст...',
                           }))
    files = forms.FileField(label='Выберите файлы', required=False,
                            widget=forms.ClearableFileInput(attrs={
                                'multiple': True,
                            }))
    student = None

    def __init__(self, *args, **kwargs):
        global student
        student = kwargs.pop('student', None)
        if student is None:
            raise Exception('student=None')
        kwargs.setdefault('label_suffix', '')
        super(CompletedTaskAddForm, self).__init__(*args, **kwargs)
        self.fields['task'].queryset = models.Task.objects.filter(teacher_subjects__in=student.teacher_subjects.all())

    @transaction.atomic
    def save(self, commit=True):
        completed_task = super().save(commit=False)
        completed_task.student = student
        completed_task.save()
        return completed_task

    class Meta:
        model = models.CompletedTask
        fields = ['task', 'text', 'files']


class MarkAddForm(forms.ModelForm):
    task = forms.ModelChoiceField(required=False,
                                  queryset=models.Task.objects.none(),
                                  label='Задание',
                                  empty_label='Выберите задание',
                                  widget=forms.Select(attrs={
                                      'class': 'mdb-select',
                                      'searchable': 'Пойск',
                                  }))
    student_teacher_subject = forms.ModelChoiceField(required=True,
                                                     label='Студент',
                                                     queryset=models.StudentTeacherSubject.objects.none(),
                                                     widget=forms.Select(attrs={
                                                         'class': 'mdb-select',
                                                         'searchable': 'Пойск',
                                                     }))
    points = forms.FloatField(required=True,
                              label='Баллы',
                              validators=[MinValueValidator(-100), MaxValueValidator(100)],
                              widget=forms.NumberInput(attrs={
                                  'class': 'form-control',
                                  'min': '-100',
                                  'max': '100',
                                  'placeholder': '-',
                              }))

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        task = kwargs.pop('task', None)
        if course and task:
            raise Exception('Не указан курс(course=None) и задание (task=None) одновременно')
        kwargs.setdefault('label_suffix', '')
        super(MarkAddForm, self).__init__(*args, **kwargs)
        if task is None:
            self.fields['task'].queryset = models.Task.objects.filter(teacher_subjects=course)
            self.fields['student_teacher_subject'].queryset = \
                models.StudentTeacherSubject.objects.filter(teacher_subject=course)
        else:
            students_has_courses = models.StudentTeacherSubject.objects.filter(
                teacher_subject__in=task.teacher_subjects.all()
            )
            self.fields['student_teacher_subject'].queryset = students_has_courses
            self.fields['task'].queryset = models.Task.objects.filter(pk=task.pk)
    # students = list(dict.fromkeys([(student.student.pk, student.student) for student in students_has_courses]))
    # students.sort(key=lambda tup: (tup[1].user.last_name, tup[1].pk))

    class Meta:
        model = models.Mark
        fields = ['task', 'student_teacher_subject', 'points']


class SettingsForm(forms.ModelForm):
    patronymic = forms.CharField(max_length=256, required=False, label='Отчество', widget=forms.TextInput(attrs={
        'class': 'form-control mb-3',
        'placeholder': 'Введите отчество',
    }))

    email = forms.EmailField(required=False, label='Почта', widget=forms.TextInput(attrs={
        'class': 'form-control mb-3',
        'placeholder': 'Введите почту',
    }))
    avatar = forms.FileField(
        widget=forms.FileInput(),
        required=False, label='Аватар'
    )

    class Meta:
        model = models.User
        fields = ['patronymic', 'email', 'avatar']

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        if avatar.__class__.__name__ == 'ImageFieldFile':
            return avatar
        try:
            w, h = get_image_dimensions(avatar)

            # validate dimensions
            min_width = min_height = 300
            if w < min_width or h < min_height:
                raise forms.ValidationError(u'Please use an image that is %s x %s pixels or bigger.'
                                            % (min_width, min_height))

            if w / h > 1.05 or w / h < 0.95:
                raise forms.ValidationError(u'Пожалуйста используйте квадратную картинку')

            # validate content type
            main, sub = avatar.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'jpg', 'png']):
                raise forms.ValidationError(u'Please use a JPEG or PNG image.')

            # validate file size
            if len(avatar) > (5 * 1024 * 1024):
                raise forms.ValidationError(
                    u'Avatar file size may not exceed 20k.')

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return avatar
