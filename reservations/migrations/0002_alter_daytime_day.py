# Generated by Django 4.2.6 on 2023-11-17 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='daytime',
            name='day',
            field=models.CharField(choices=[(0, 'Δευτέρα'), (1, 'Τρίτη'), (2, 'Τετάρτη'), (3, 'Πέμπτη'), (4, 'Παρασκευή'), (5, 'Σάββατο'), (6, 'Κυριακή')], max_length=9),
        ),
    ]