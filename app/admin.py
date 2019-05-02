from django.contrib import admin
import app.models as models
from django.contrib.auth.admin import UserAdmin

admin.site.register(models.User)

admin.site.register(models.Student)
admin.site.register(models.Teacher)
admin.site.register(models.Subject)
admin.site.register(models.TeacherSubject)
admin.site.register(models.StudentTeacherSubject)
admin.site.register(models.Task)
admin.site.register(models.TaskFile)
admin.site.register(models.Mark)
admin.site.register(models.Specialty)
admin.site.register(models.Group)
