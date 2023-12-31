# Generated by Django 4.2.6 on 2023-11-18 21:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0010_schoolyear_reservationperiod_schoolyear'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2023, 11, 18, 21, 49, 23, 185743, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservation',
            name='is_performed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='reservation',
            name='status',
            field=models.CharField(choices=[('pending', 'Εκκρεμής'), ('denied', 'Ακυρωμένη'), ('approved', 'Επιβεβαιωμένη')], default='pending', max_length=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reservation',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
