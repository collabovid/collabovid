import json

from django.db.models import QuerySet, Count, Value
from django.db.models.functions import Concat

from data.models import Journal, Author, GeoLocation, Topic


class TagifySearchable:
    """
    Base class for searchable items that are displayed in the tagify environment.
    The main purpose of this class is to convert given objects into the desired json.
    """

    @staticmethod
    def from_ids(ids):
        return NotImplementedError

    @property
    def dict(self):
        raise NotImplementedError()

    @property
    def json(self):
        return json.dumps(self.dict)


class JournalSearchable(TagifySearchable):

    def __init__(self, journals: QuerySet):
        self._journals = journals

    @staticmethod
    def from_ids(ids):
        if ids:
            return JournalSearchable(Journal.objects.filter(pk__in=ids) \
                                     .annotate(paper_count=Count('papers')).order_by('-paper_count'))
        else:
            return JournalSearchable(Journal.objects.none())

    @property
    def dict(self):
        return [{"pk": journal.pk,
                 "value": journal.displayname,
                 "count": journal.paper_count} for journal in self._journals]


class AuthorSearchable(TagifySearchable):

    def __init__(self, authors: QuerySet):
        self._authors = authors

    @staticmethod
    def from_ids(ids):
        if ids:
            return AuthorSearchable(Author.objects.filter(pk__in=ids))
        else:
            return AuthorSearchable(Author.objects.none())

    @staticmethod
    def single_object(author):
        return {"value": author.full_name,
                 "pk": author.pk}

    @property
    def dict(self):
        return [self.single_object(author) for author in self._authors]


class LocationSearchable(TagifySearchable):

    def __init__(self, locations: QuerySet):
        self._locations = locations

    @staticmethod
    def from_ids(ids):
        if ids:
            return LocationSearchable(
                GeoLocation.objects.filter(pk__in=ids).annotate(paper_count=Count('papers'))
                    .order_by('-paper_count'))
        else:
            return LocationSearchable(GeoLocation.objects.none())

    @property
    def dict(self):
        return [{"pk": location.pk,
                 "value": location.displayname,
                 "count": location.paper_count} for location in self._locations]


class TopicSearchable(TagifySearchable):

    def __init__(self, topics: QuerySet):
        self._topics = topics

    @staticmethod
    def from_ids(ids):
        if ids:
            return TopicSearchable(Topic.objects.filter(pk__in=ids))
        else:
            return TopicSearchable(Topic.objects.none())

    @staticmethod
    def single_object(topic):
        return {"value": topic.name,
                 "pk": topic.pk}

    @property
    def dict(self):
        return [self.single_object(topic=topic) for topic in self._topics]