from django import template
import math

register = template.Library()


@register.filter
def round_up(value):
    if value and isinstance(value, float):
        return int(math.ceil(value))
    else:
        return value