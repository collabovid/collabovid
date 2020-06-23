from django import template
from search.tagify.tagify_searchable import *
register = template.Library()


@register.filter()
def journals_to_json(value):
    return JournalSearchable.from_ids(value).json


@register.filter()
def authors_to_json(value):
    return AuthorSearchable.from_ids(value).json


@register.filter()
def locations_to_json(value):
    return LocationSearchable.from_ids(value).json
