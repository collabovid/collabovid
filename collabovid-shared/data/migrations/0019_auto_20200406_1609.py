# Generated by Django 3.0.4 on 2020-04-06 16:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0018_auto_20200331_1554'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaperData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(default=None, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='paper',
            name='data',
            field=models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paper', to='data.PaperData'),
        ),
    ]
