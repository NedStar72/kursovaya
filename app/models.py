from django.db import models
from django import forms

class Student(models.Model):
    name = models.CharField(max_length=30)
    #Добавить другие данные (и как делаить пользователей на student/не student?

class Сourse(models.Model):
    name = models.CharField(max_length=30)
    year = models.IntegerField()
    semester = models.IntegerField()
    students = models.ManyToManyField()

class Task(models.Model):
    name = models.CharField(max_length=40)
    text = models.TextField()
    curse = models.ForeignKey(Сourse, on_delete=models.CASCADE)
    #files = models.FileField(upload_to='documents/%Y/%m/%d', widget=forms.ClearableFileInput(attrs={'multiple': True}))
    #Надо ли добавить модель сданные задания?