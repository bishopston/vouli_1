# Generated by Django 4.2.6 on 2023-11-03 12:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0007_alter_schooluser_department'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schooluser',
            name='email',
        ),
    ]