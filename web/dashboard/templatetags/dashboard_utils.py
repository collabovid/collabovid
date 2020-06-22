from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def sort(lst):
    return sorted(lst)
