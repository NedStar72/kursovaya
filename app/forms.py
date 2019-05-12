import datetime, collections
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm as _UserCreationForm
from django.db import transaction
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
    f_name = forms.CharField(max_length=256, required=True, label='Имя')
    s_name = forms.CharField(max_length=256, required=True, label='Фамилия')
    t_name = forms.CharField(max_length=256, required=False, label='Отчество')
    email = forms.EmailField(required=False)

    class Meta(_UserCreationForm.Meta):
        model = models.User

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit)
        user.first_name = self.cleaned_data["f_name"]
        user.last_name = self.cleaned_data["s_name"]
        user.patronymic = self.cleaned_data["t_name"]
        user.EMAIL_FIELD = self.cleaned_data["email"]
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
    dayOfWeek = forms.ChoiceField(required=True,
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
    students = forms.MultipleChoiceField(choices=[(x.user.pk, x.user.last_name + ' ' + x.user.first_name) for x in models.Student.objects.all()],
                                         label='Студенты',
                                         required=True,
                                         widget=forms.SelectMultiple(attrs={
                                             'class': 'mdb-select',
                                             'multiple': '',
                                             'searchable': 'Пойск',
                                         }))

    class Meta:
        model = models.StudentTeacherSubject
        fields = ['subject', 'dayOfWeek', 'time', 'teacher', 'students']

    @transaction.atomic
    def save(self, commit=True):
        course_l = models.TeacherSubject.objects.create(teacher=models.Teacher.objects.get(pk=int(self.cleaned_data.get('teacher'))),
                                                        subject=models.Subject.objects.get(pk=int(self.cleaned_data.get('subject'))),
                                                        dayOfWeek=self.cleaned_data.get('dayOfWeek'),
                                                        time=datetime.datetime.strptime(self.cleaned_data.get('time'), '%H:%M').time())
        for student in self.cleaned_data.get('students'):
            models.StudentTeacherSubject.objects.create(student=models.Student.objects.get(pk=int(student)),
                                                        teacher_subject=course_l)
        return models.StudentTeacherSubject.objects.latest('pk')


class TaskAddForm(forms.ModelForm):
    name = forms.CharField(max_length=254, label='Название',
                           widget=forms.TextInput(attrs={
                               'class': 'form-control',
                               'placeholder': 'Введите название',
                           }))

    end_date = forms.DateField(label='Дата окончания', input_formats=['%d/%m/%Y'],
                               widget=forms.DateInput(attrs={
                                   'class': 'form-control datepicker',
                                   'placeholder': 'Выберите дату',
                               }))

    files = forms.FileField(label='Выберите файлы', required=False,
                            widget=forms.ClearableFileInput(attrs={
                                'multiple': True,
                            }))

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        teacher = kwargs.pop('teacher', 0)
        super(TaskAddForm, self).__init__(*args, **kwargs)
        self.fields['taught_subjects'] = forms.MultipleChoiceField(
            choices=[(x.pk, x.subject.__str__() + ' (' + x.get_day() + ', ' + x.time.strftime('%H:%M') + ')')
                     for x in models.TeacherSubject.objects.filter(teacher=teacher)],
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
        fields = ['name', 'taught_subjects', 'end_date', 'text', 'files']
        labels = {
            'text': 'Текст',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
            }),
        }
