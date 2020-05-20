from django import template
from colour import Color
from math import floor
red = Color("red")
white = Color("white")
progress_color_range = list(red.range_to(Color("green"), 100))
text_color_range = list(white.range_to(Color("black"), 100))

register = template.Library()


@register.filter
def score_badge_color(value):
    index = floor(float(value))
    return progress_color_range[index].hex


@register.filter
def score_text_color(value):
    index = floor(float(value))
    return text_color_range[index].hex


@register.filter
def score_text(value):
    if value > 60:
        return "Good Match"
    elif value > 40:
        return "Okay Match"
    elif value > 20:
        return "Matches"
    else:
        return "Almost no match"
