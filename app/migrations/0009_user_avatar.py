# Generated by Django 2.2 on 2019-05-22 11:52

import app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20190522_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(null=True, upload_to=app.models.user_avatar_path),
        ),
    ]
