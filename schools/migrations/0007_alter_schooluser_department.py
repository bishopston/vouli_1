# Generated by Django 4.2.6 on 2023-10-31 21:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0006_schooluser_department'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schooluser',
            name='department',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='schools.department'),
        ),
    ]