# Generated by Django 4.2.6 on 2023-11-20 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0014_reservation_reservation_period_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservation',
            name='reservation_window',
        ),
        migrations.AlterField(
            model_name='reservationwindow',
            name='end_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='reservationwindow',
            name='start_date',
            field=models.DateTimeField(),
        ),
    ]
