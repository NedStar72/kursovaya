# Generated by Django 2.2 on 2019-05-17 13:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20190517_1836'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'default_related_name': 'tasks', 'ordering': ['end_date', 'start_date', 'name'], 'verbose_name': 'Задание', 'verbose_name_plural': 'Задания'},
        ),
        migrations.RenameField(
            model_name='task',
            old_name='is_meek',
            new_name='is_reciprocal',
        ),
    ]
