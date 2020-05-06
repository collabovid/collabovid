from django.db import models
from django.db.models import Q, Max
from django.utils.dateparse import parse_date
from django.db.models import F
import logging
import re
class Topic(models.Model):
    name = models.CharField(default="Unknown", max_length=300)
    description = models.TextField()
    description_html = models.TextField()
    icon_path = models.CharField(max_length=100, default="")

    latent_topic_score = models.BinaryField(null=True)


class PaperHost(models.Model):
    name = models.CharField(max_length=60)
    url = models.URLField()


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    citation_count = models.IntegerField(null=True, default=None)
    citations_last_update = models.DateTimeField(null=True, default=None)
    scholar_url = models.URLField(null=True, default=None)

    class Meta:
        ordering = [F('citation_count').desc(nulls_last=True)]


class Category(models.Model):
    """
    e.g. Microbiology
    """
    name = models.CharField(max_length=200, primary_key=True)


class PaperData(models.Model):
    """
    Model to store large data which should not be loaded on each select on a regular Paper
    """

    content = models.TextField(null=True, default=None)

class Paper(models.Model):
    SORTED_BY_TOPIC_SCORE = 1
    SORTED_BY_NEWEST = 2
    SORTED_BY_SCORE = 3

    preview_image = models.ImageField(upload_to="pdf_images", null=True, default=None)

    doi = models.CharField(max_length=100, primary_key=True)

    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, related_name="publications")
    category = models.ForeignKey(Category, related_name="papers", on_delete=models.CASCADE)
    host = models.ForeignKey(PaperHost, related_name="papers", on_delete=models.CASCADE)
    version = models.IntegerField(default=1, null=False)

    data = models.OneToOneField(PaperData, null=True, default=None, related_name='paper', on_delete=models.SET_NULL)

    topic = models.ForeignKey(Topic,
                              related_name="papers",
                              null=True,
                              default=None,
                              on_delete=models.SET_DEFAULT)
    topic_score = models.FloatField(default=0.0)
    abstract = models.TextField()

    url = models.URLField()
    pdf_url = models.URLField()
    is_preprint = models.BooleanField(default=True)

    published_at = models.DateField()

    latent_topic_score = models.BinaryField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scrape = models.DateTimeField(null=True, default=None)

    @property
    def percentage_topic_score(self):
        return round(self.topic_score * 100)