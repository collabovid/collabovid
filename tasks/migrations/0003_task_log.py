# Generated by Django 3.0.4 on 2020-05-02 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_auto_20200418_0915'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='log',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
