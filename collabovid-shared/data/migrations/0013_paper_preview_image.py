# Generated by Django 3.0.4 on 2020-03-29 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0012_auto_20200329_1850'),
    ]

    operations = [
        migrations.AddField(
            model_name='paper',
            name='preview_image',
            field=models.ImageField(default=None, null=True, upload_to='static/pdf_images'),
        ),
    ]
