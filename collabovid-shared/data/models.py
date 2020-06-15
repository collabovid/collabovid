from typing import Union

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils.translation import gettext_lazy
from django.db.models import Q


class Topic(models.Model):
    name = models.CharField(default="Unknown", max_length=300)
    description = models.TextField()
    description_html = models.TextField()
    icon_path = models.CharField(max_length=100, default="")


class PaperHost(models.Model):
    name = models.CharField(max_length=60, unique=True)
    url = models.URLField(null=True, default=None)


class DataSource(models.IntegerChoices):
    MEDBIORXIV = 0, gettext_lazy('medbioRxiv')
    ARXIV = 1, gettext_lazy('arXiv')
    PUBMED = 2, gettext_lazy('pubmed')
    ELSEVIER = 3, gettext_lazy('elsevier')

    @property
    def priority(self):
        if self.value == DataSource.MEDBIORXIV:
            return 0
        if self.value == DataSource.ARXIV:
            return 1
        elif self.value == DataSource.PUBMED:
            return 10
        elif self.value == DataSource.ELSEVIER:
            return 5
        else:
            return 100

    @property
    def check_covid_related(self):
        if self.value == DataSource.MEDBIORXIV:
            return False
        else:
            return True

    @staticmethod
    def compare(first: Union[int, None], second: Union[int, None]):
        if second is None and first is None:
            return 0
        elif second is None:
            return 1
        elif first is None:
            return -1

        return DataSource(first).priority < DataSource(second).priority


class Journal(models.Model):
    name = models.CharField(max_length=200, unique=True)
    alias = models.CharField(max_length=200, null=True, default=None, blank=True)
    url = models.URLField(null=True, default=None, blank=True)

    @property
    def displayname(self):
        return self.alias if self.alias else self.name

    @staticmethod
    def max_length(field: str):
        return Journal._meta.get_field(field).max_length

    @staticmethod
    def cleanup():
        deleted, _ = Journal.objects.filter(papers=None).delete()
        return deleted


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    @staticmethod
    def max_length(field: str):
        return Author._meta.get_field(field).max_length

    @staticmethod
    def cleanup():
        deleted, _ = Author.objects.filter(publications=None).delete()
        return deleted


class Category(models.Model):
    """
    Papers will be categorized with machine learning algorithms.
    """
    name = models.CharField(max_length=200)
    description = models.TextField()
    model_identifier = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#F0F0F0")


class PaperData(models.Model):
    """
    Model to store large data which should not be loaded on each select on a regular Paper
    """
    content = models.TextField(null=True, default=None)

    @staticmethod
    def cleanup():
        used_paper_ids = [p.data_id for p in Paper.objects.all() if p.data_id]
        deleted, _ = PaperData.objects.exclude(id__in=used_paper_ids).delete()
        return deleted


class VerificationState(models.IntegerChoices):
    REJECTED = 0, gettext_lazy('rejected')
    AUTOMATICALLY_REJECTED = 1, gettext_lazy('rejected automatically')
    UNKNOWN = 2, gettext_lazy('unknown')
    AUTOMATICALLY_ACCEPTED = 3, gettext_lazy('added automatically')
    ACCEPTED = 4, gettext_lazy('accepted')


class GeoLocation(models.Model):
    name = models.CharField(max_length=100, null=False)
    alias = models.CharField(max_length=40, null=True)
    latitude = models.FloatField(null=False)
    longitude = models.FloatField(null=False)

    @property
    def displayname(self):
        return self.alias if self.alias else self.name

    def __eq__(self, other):
        return isinstance(other, GeoLocation) and self.pk == other.pk


class GeoCountry(GeoLocation):
    alpha_2 = models.CharField(max_length=2)

    @property
    def papers(self):
        return Paper.objects.filter(Q(locations=self) | Q(locations__in=GeoCity.objects.filter(country=self)))


class GeoCity(GeoLocation):
    country = models.ForeignKey(GeoCountry, related_name="cities", on_delete=models.CASCADE)


class GeoStopword(models.Model):
    word = models.CharField(max_length=50)

class Paper(models.Model):
    SORTED_BY_TOPIC_SCORE = 1
    SORTED_BY_NEWEST = 2
    SORTED_BY_SCORE = 3

    preview_image = models.ImageField(upload_to="pdf_images", null=True, default=None)

    doi = models.CharField(max_length=100, primary_key=True)

    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, related_name="publications")
    categories = models.ManyToManyField(Category, related_name="papers", through='CategoryMembership')
    host = models.ForeignKey(PaperHost, related_name="papers", on_delete=models.CASCADE)
    data_source_value = models.IntegerField(choices=DataSource.choices)
    version = models.CharField(max_length=40, null=True, default=None)

    data = models.OneToOneField(PaperData, null=True, default=None, related_name='paper', on_delete=models.SET_NULL)

    pubmed_id = models.CharField(max_length=20, unique=True, null=True, default=None)

    topic = models.ForeignKey(Topic,
                              related_name="papers",
                              null=True,
                              default=None,
                              on_delete=models.SET_DEFAULT)
    covid_related = models.BooleanField(null=True, default=None)
    topic_score = models.FloatField(default=0.0)
    abstract = models.TextField()

    url = models.URLField(null=True, default=None)
    pdf_url = models.URLField(null=True, default=None)
    is_preprint = models.BooleanField(default=True)

    published_at = models.DateField(null=True, default=None)
    journal = models.ForeignKey(Journal, related_name="papers", on_delete=models.CASCADE, null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scrape = models.DateTimeField(null=True, default=None)

    locations = models.ManyToManyField(GeoLocation, related_name="papers", through="GeoLocationMembership")


    @property
    def percentage_topic_score(self):
        return round(self.topic_score * 100)

    def add_preview_image(self, pillow_image, save=True):
        img_name = self.doi.replace('/', '_').replace('.', '_').replace(',', '_').replace(':', '_') + '.jpg'
        self.preview_image.save(img_name, InMemoryUploadedFile(pillow_image, None, img_name,
                                                               'image/jpeg', pillow_image.tell, None),
                                save=save)

    @staticmethod
    def max_length(field: str):
        return Paper._meta.get_field(field).max_length


class GeoLocationMembership(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    location = models.ForeignKey(GeoLocation, on_delete=models.CASCADE)
    word = models.CharField(max_length=50)
    state = models.IntegerField(choices=VerificationState.choices)


class CategoryMembership(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
