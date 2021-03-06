# Generated by Django 3.0.7 on 2020-07-21 07:27

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0049_auto_20200714_1210'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorNameResolution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_first_name', models.TextField(max_length=50)),
                ('source_last_name', models.TextField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='ScrapeConflict',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datapoint', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
        ),
        migrations.RemoveField(
            model_name='paperhost',
            name='url',
        ),
        migrations.AddField(
            model_name='paper',
            name='manually_modified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='paper',
            name='scrape_hash',
            field=models.CharField(default=None, max_length=22, null=True),
        ),
        migrations.AlterField(
            model_name='paper',
            name='data',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paper', to='data.PaperData'),
        ),
        migrations.AlterField(
            model_name='paper',
            name='journal',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='papers', to='data.Journal'),
        ),
        migrations.AlterField(
            model_name='paper',
            name='pdf_url',
            field=models.URLField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='paper',
            name='preview_image',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='pdf_images'),
        ),
        migrations.AlterField(
            model_name='paper',
            name='pubmed_id',
            field=models.CharField(blank=True, default=None, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='paper',
            name='topic',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='papers', to='data.Topic'),
        ),
        migrations.AlterField(
            model_name='paper',
            name='url',
            field=models.URLField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='paper',
            name='version',
            field=models.CharField(blank=True, default=None, max_length=40, null=True),
        ),
        migrations.AddIndex(
            model_name='author',
            index=models.Index(fields=['last_name', 'first_name'], name='data_author_last_na_d01e12_idx'),
        ),
        migrations.AddField(
            model_name='scrapeconflict',
            name='paper',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Paper'),
        ),
        migrations.AddField(
            model_name='authornameresolution',
            name='target_author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='data.Author'),
        ),
        migrations.AddIndex(
            model_name='authornameresolution',
            index=models.Index(fields=['source_last_name', 'source_first_name'], name='data_author_source__2ad6dc_idx'),
        ),
    ]
