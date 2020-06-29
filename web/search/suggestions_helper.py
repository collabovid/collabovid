from django.db.models import When, Value, Case, IntegerField


class SuggestionsHelper:

    @staticmethod
    def compute_suggestions(model, search, query, field, size=6):
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