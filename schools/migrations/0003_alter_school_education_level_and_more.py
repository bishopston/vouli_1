# Generated by Django 4.2.6 on 2023-10-29 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0002_alter_school_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='education_level',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='school',
            name='legal_character',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='school',
            name='ota_municipality',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='school',
            name='periphery',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AlterField(
            model_name='school',
            name='type',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
