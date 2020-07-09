from django import template
from django.urls import reverse
from data.models import Paper, Author, Journal, Topic
from django.utils.safestring import mark_safe
import re

register = template.Library()

SLICE_DIFFERENCE = 20


@register.filter
def edit_object_link(user, object):
    """
    Renders links for editing certain objects in the django admin panel once the current user is authenticated
    and member of the staff.
    :param user:
    :param object:
    :return:
    """

    if user.is_authenticated and user.is_staff:
        url = None
        if isinstance(object, Paper):
            url = reverse("admin:data_paper_change", args=(object.pk,))
        elif isinstance(object, Author):
            url = reverse("admin:data_author_change", args=(object.pk,))
        elif isinstance(object, Journal):
            url = reverse("admin:data_journal_change", args=(object.pk,))
        elif isinstance(object, Topic):
            url = reverse("admin:data_topic_change", args=(object.pk,))

        if url:
            return mark_safe("<sup><a href='{}'>[Edit]</a></sup>".format(url))

    return ""


def get_next_preview_size(paper, size):
    starting_em = [i.start() for i in re.finditer('<em>', paper.abstract)]
    ending_em = [i.end() for i in re.finditer('</em>', paper.abstract)]

    for start, end in zip(starting_em, ending_em):
        if start-SLICE_DIFFERENCE < size < end+SLICE_DIFFERENCE:
            size = end + SLICE_DIFFERENCE

    return size


@register.filter
def abstract_preview_size_mobile(paper):
    return get_next_preview_size(paper, 150)


@register.filter
def abstract_preview_size(paper):
    return get_next_preview_size(paper, 420) if paper.preview_image and len(paper.preview_image) > 0 else get_next_preview_size(paper, 900)


@register.filter
def preview_slice(paper, mobile=False):
    slice_size_func = abstract_preview_size_mobile if mobile else abstract_preview_size
    return paper.abstract[:slice_size_func(paper)-SLICE_DIFFERENCE]


@register.filter
def full_text_slice(paper, mobile=False):
    slice_size_func = abstract_preview_size_mobile if mobile else abstract_preview_size
    return paper.abstract[slice_size_func(paper)-SLICE_DIFFERENCE:]
