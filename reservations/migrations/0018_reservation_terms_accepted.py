# Generated by Django 4.2.7 on 2023-11-24 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0017_remove_reservation_creator_reservation_schooluser'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='terms_accepted',
            field=models.BooleanField(default=False),
        ),
    ]
