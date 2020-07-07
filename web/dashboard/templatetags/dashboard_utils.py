from django.template.defaulttags import register


@register.filter
def sort(lst):
    return sorted(lst)
