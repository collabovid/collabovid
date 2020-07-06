from django.db.models import When, Value, Case, IntegerField
from django.conf import settings
from data.models import Author, Journal, GeoLocation
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Concat, Greatest
from django.db.models import Count, Max


class SuggestionsHelper:

    @staticmethod
    def compute_postgres_suggestions(model, query, size=6):

        if not query:
            return model.objects.none()

        if model == Author:
            possible_authors = Author.objects.all().annotate(name=Concat('first_name', Value(' '), 'last_name'))
            return possible_authors.annotate(similarity=TrigramSimilarity('name', query)).order_by(
                '-similarity')[:size]
        elif model == Journal:
            return Journal.objects.all().annotate(paper_count=Count('papers')).annotate(
                similarity_name=TrigramSimilarity('name', query)).annotate(
                similarity_alias=TrigramSimilarity('alias', query)).annotate(
                similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:size]
        elif model == GeoLocation:
            locations = GeoLocation.objects.all().annotate(paper_count=Count('papers'))
            return locations.annotate(similarity_name=TrigramSimilarity('name', query)).annotate(
                similarity_alias=TrigramSimilarity('alias', query)).annotate(
                similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:size]

    @staticmethod
    def compute_elasticsearch_suggestions(model, search, query, field, size=6):
        if not query:
            return model.objects.none()

        suggestions = search.suggest("autocomplete", query, completion={
            'field': field, 'size': size}).execute().suggest
        ids = []
        ordering = []

        for i, option in enumerate(suggestions.autocomplete[0].options):
            pk = option['_id']
            ordering.append(When(pk=pk, then=Value(i)))
            ids.append(pk)

        return model.objects.filter(pk__in=ids).annotate(
            ordering=Case(*ordering, output_field=IntegerField())).order_by('ordering')
