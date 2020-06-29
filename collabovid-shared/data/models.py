from typing import Union

import pycountry
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils.translation import gettext_lazy
from django.db.models import Q, Subquery, OuterRef, Value, Count
from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver


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
        used_data_ids = [p.data_id for p in Paper.objects.all() if p.data_id]
        deleted, _ = PaperData.objects.exclude(id__in=used_data_ids).delete()
        return deleted


class VerificationState(models.IntegerChoices):
    REJECTED = 0, gettext_lazy('rejected')
    AUTOMATICALLY_REJECTED = 1, gettext_lazy('rejected automatically')
    UNKNOWN = 2, gettext_lazy('unknown')
    AUTOMATICALLY_ACCEPTED = 3, gettext_lazy('added automatically')
    ACCEPTED = 4, gettext_lazy('accepted')


class GeoLocation(models.Model):
    geonames_id = models.IntegerField(unique=True, primary_key=False)
    name = models.CharField(max_length=100, null=False)
    alias = models.CharField(max_length=40, null=True, blank=True)
    latitude = models.FloatField(null=False)
    longitude = models.FloatField(null=False)

    count = models.IntegerField(default=0)

    @staticmethod
    def get_or_create_from_geonames_object(geonames_object):
        try:
            db_country = GeoCountry.objects.get(alpha_2=geonames_object.country_code)
            created = False
        except GeoCountry.DoesNotExist:
            db_country = GeoCountry.objects.create(
                geonames_id=geonames_object.country.id,
                name=geonames_object.country.name,
                alias=pycountry.countries.get(alpha_2=geonames_object.country.country_code).name,
                alpha_2=geonames_object.country.country_code,
                latitude=geonames_object.country.latitude,
                longitude=geonames_object.country.longitude,
            )
            created = True

        if geonames_object.feature_label.startswith('A.PCL'):
            return db_country, created
        else:
            try:
                return GeoCity.objects.get(geonames_id=geonames_object.id), False
            except GeoCity.DoesNotExist:
                db_location = GeoCity.objects.create(
                    geonames_id=geonames_object.id,
                    name=geonames_object.name,
                    country=db_country,
                    latitude=geonames_object.latitude,
                    longitude=geonames_object.longitude,
                )
                return db_location, created

    @property
    def is_city(self):
        return hasattr(self, 'geocity')


    @property
    def is_country(self):
        return hasattr(self, 'geocountry')

    @property
    def displayname(self):
        return self.alias if self.alias else self.name

    #
    # def __eq__(self, other):
    #     return isinstance(other, GeoLocation) and self.pk == other.pk

    @staticmethod
    def recompute_counts(cities, countries):
        count_for_country = Subquery(Paper.objects.annotate(country=OuterRef('pk'))
                                     .filter(Q(locations=OuterRef('pk')) |
                                             Q(locations__in=Subquery(
                                                 GeoCity.objects.filter(country=OuterRef('country')).only('pk')))).
                                     annotate(group=Value('Paper')).values('group')
                                     .annotate(count=Count("pk", distinct=True)).values('count'),
                                     output_field=models.IntegerField())

        cities.update(count=Subquery(
            Paper.objects.filter(locations=OuterRef('pk')).annotate(group=Value('Paper')).values('group').annotate(
                count=Count('pk')).values('count'),
            output_field=models.IntegerField()))
        countries.update(count=count_for_country)


class GeoCountry(GeoLocation):
    alpha_2 = models.CharField(max_length=2, unique=True)

    @property
    def papers(self):
        return Paper.objects.filter(Q(locations=self) | Q(locations__in=GeoCity.objects.filter(country=self)))


class GeoCity(GeoLocation):
    country = models.ForeignKey(GeoCountry, related_name="cities", on_delete=models.CASCADE)


class GeoNameResolution(models.Model):
    source_name = models.CharField(unique=True, max_length=50)
    target_geonames_id = models.IntegerField(null=True, default=None)


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
    location_modified = models.BooleanField(default=False)

    @property
    def countries(self):
        return GeoCountry.objects.filter(Q(pk__in=self.locations.all()) | Q(pk__in=self.cities.values('country')))

    @property
    def cities(self):
        return GeoCity.objects.filter(pk__in=self.locations.all())

    @property
    def ordered_locations(self):
        result = []
        cities = list(self.cities.all())
        for country in self.countries.all():
            country_cities = [city for city in cities if city.country == country]
            if country_cities:
                result.append(country)
                result += country_cities
            else:
                result.insert(0, country)
        return result

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
    word = models.CharField(max_length=50, null=True, default=None)
    state = models.IntegerField(choices=VerificationState.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['paper', 'location'], name='Paper and Location')
        ]


class CategoryMembership(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)


def locations_changed(instance, reverse, pk_set, action, **kwargs):
    if action in ["post_add", "post_remove"]:
        if reverse:
            #  Given instance is either a city or a country which has added one or more papers
            cities = GeoCity.objects.filter(pk=instance.pk)
            countries = GeoCountry.objects.filter(Q(pk=instance.pk) | Q(cities=instance.pk)).distinct()
        else:
            #  Given instance is a Paper that has added one or more locations.
            cities = GeoCity.objects.filter(pk__in=pk_set)
            countries = GeoCountry.objects.filter(Q(pk__in=pk_set) | Q(cities__in=cities)).distinct()

        GeoLocation.recompute_counts(cities, countries)

    elif action in ["pre_clear", "post_clear"]:
        raise NotImplementedError("Clearing the location membership relation is not supported yet.")


def membership_changed(sender, instance, **kwargs):
    """
    In certain cases we want to prevent the model from recomputing the count.
    In that cases set prevent_recompute_count
    """
    if not hasattr(instance, 'prevent_recompute_count') or not instance.prevent_recompute_count:
        locations_changed(sender=sender,
                          instance=instance.location,
                          reverse=True,
                          action="post_add", pk_set={}, **kwargs)


m2m_changed.connect(locations_changed, sender=Paper.locations.through, dispatch_uid="models.data")
post_save.connect(membership_changed, sender=GeoLocationMembership, dispatch_uid="models.data")
post_delete.connect(membership_changed, sender=GeoLocationMembership, dispatch_uid="models.data")
