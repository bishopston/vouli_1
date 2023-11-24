# Generated by Django 4.2.7 on 2023-11-22 22:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0010_delete_schoolteam'),
        ('reservations', '0016_remove_reservation_schoolteam_reservation_amea_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservation',
            name='creator',
        ),
        migrations.AddField(
            model_name='reservation',
            name='schoolUser',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='schools.schooluser'),
        ),
    ]