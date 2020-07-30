from django import template
from django.urls import reverse
import urllib

register = template.Library()


def search_url_with_querystring(**kwargs):
    new_parameters = {}
    for name, value in kwargs.items():
        if type(value) == list:
            if len(value) > 0:
                new_parameters[name] = ','.join(map(str, value))
        else:
            new_parameters[name] = value
    return reverse('search') + '?' + urllib.parse.urlencode(new_parameters)


@register.filter()
def search_url_from_dict(value):
    return search_url_with_querystring(**value)


@register.filter()
def search_url_from_category(value):
    return search_url_with_querystring(categories=[value])


@register.filter()
def search_url_from_location(value):
    return search_url_with_querystring(locations=[value])


@register.filter()
def search_url_from_sorted_by(value):
    return search_url_with_querystring(sorted_by=value)


@register.filter()
def search_url_from_topic(value):
    return search_url_with_querystring(topics=[value])
