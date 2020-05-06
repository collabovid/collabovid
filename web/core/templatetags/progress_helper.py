from django import template
from colour import Color
from math import floor
red = Color("red")
progress_color_range = list(red.range_to(Color("green"), 100))

register = template.Library()

@register.filter
def progress_color(value):
    index = floor(float(value))
    return progress_color_range[index].hex
