from django.db import models
from django.db.models import Q, Max
from django.utils.dateparse import parse_date
from django.templatetags.static import static


import os
from django.conf import settings

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

    class Meta:
        ordering = ['-citation_count']


class Category(models.Model):
    """
    e.g. Microbiology
    """
    name = models.CharField(max_length=60, primary_key=True)


class Paper(models.Model):

    SORTED_BY_TITLE = 0
    SORTED_BY_GREATEST = 1
    SORTED_BY_NEWEST = 2
    SORTED_BY_TOPIC_SCORE = 3

    preview_image = models.ImageField(upload_to="pdf_images", null=True, default=None)

    doi = models.CharField(max_length=100, primary_key=True)

    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, related_name="publications")
    category = models.ForeignKey(Category, related_name="papers", on_delete=models.CASCADE)
    host = models.ForeignKey(PaperHost, related_name="papers", on_delete=models.CASCADE)

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

    @property
    def percentage_topic_score(self):
        return round(self.topic_score * 100)

    @staticmethod
    def get_paper_for_query(search_query, start_date, end_date, categories, topics, sorted_by=SORTED_BY_TITLE):
        try:
            start_date = parse_date(start_date)
        except ValueError:
            start_date = None

        try:
            end_date = parse_date(end_date)
        except ValueError:
            end_date = None

        papers = Paper.objects.filter(
            Q(topic__in=topics) & Q(category__in=categories) & (Q(title__contains=search_query) |
                                                                Q(authors__first_name__contains=search_query) |
                                                                Q(authors__last_name__contains=search_query))
            ).distinct()

        if start_date:
            papers = papers.filter(published_at__gte=start_date)

        if end_date:
            papers = papers.filter(published_at__lte=end_date)

        if sorted_by == Paper.SORTED_BY_TITLE:
            papers = papers.order_by("title")
        elif sorted_by == Paper.SORTED_BY_GREATEST:
            papers = papers.annotate(score=Max('authors__citation_count')).order_by("-score")
        elif sorted_by == Paper.SORTED_BY_NEWEST:
            papers = papers.order_by("-published_at")
        elif sorted_by == Paper.SORTED_BY_TOPIC_SCORE:
            papers = papers.order_by("-topic_score")

        return papers
