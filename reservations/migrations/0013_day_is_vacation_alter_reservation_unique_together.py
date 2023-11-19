# Generated by Django 4.2.6 on 2023-11-19 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0012_remove_reservation_user_schoolteam_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='day',
            name='is_vacation',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='reservation',
            unique_together={('reservation_date', 'timeslot')},
        ),
    ]
