# Generated by Django 3.0.7 on 2020-07-16 12:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0049_auto_20200710_1011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authornameresolution',
            name='target_author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='data.Author'),
        ),
    ]