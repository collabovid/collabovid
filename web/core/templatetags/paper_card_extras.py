from django import template
register = template.Library()

SLICE_DIFFERENCE = 20


@register.filter
def abstract_preview_size(paper):
    return 420 if paper.preview_image and len(paper.preview_image) > 0 else 900


@register.filter
def preview_slice(paper):
    return paper.abstract[:abstract_preview_size(paper)-SLICE_DIFFERENCE]


@register.filter
def full_text_slice(paper):
    return paper.abstract[abstract_preview_size(paper)-SLICE_DIFFERENCE:]
