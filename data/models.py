from django.db import models
from django.db.models import Q
from django.utils.dateparse import parse_date


class Topic(models.Model):
    name = models.CharField(default="Unknown", max_length=60)
    description = models.TextField()

    latent_topic_score = models.BinaryField(null=True)


class PaperHost(models.Model):
    name = models.CharField(max_length=60)
    url = models.URLField()


class Author(models.Model):
    CITATIONS_AUTHOR_NOT_FOUND = -2
    CITATIONS_NOT_SCRAPED = -1

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    citation_count = models.IntegerField(default=CITATIONS_NOT_SCRAPED)


class Category(models.Model):
    """
    e.g. Microbiology
    """
    name = models.CharField(max_length=60, primary_key=True)


class Paper(models.Model):

    doi = models.CharField(max_length=100, primary_key=True)

    title = models.CharField(max_length=200)
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
    def cleaned_doi(self):
        return self.doi.replace("/", "").replace(".", "")

    @property
    def image_name(self):
        return self.cleaned_doi + '.jpg'

    @property
    def percentage_topic_score(self):
        return round(self.topic_score * 100)

    @staticmethod
    def get_paper_for_query(search_query, start_date, end_date, categories):
        try:
            start_date = parse_date(start_date)
        except ValueError:
            start_date = None

        try:
            end_date = parse_date(end_date)
        except ValueError:
            end_date = None

        papers = Paper.objects.filter(Q(category__in=categories) & (Q(title__contains=search_query) |
                                                                    Q(authors__first_name__contains=search_query) |
                                                                    Q(authors__last_name__contains=search_query))
                                      ).distinct()

        if start_date:
            papers = papers.filter(published_at__gte=start_date)

        if end_date:
            papers = papers.filter(published_at__lte=end_date)

        return papers

