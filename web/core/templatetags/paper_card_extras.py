from django import template
register = template.Library()


@register.filter
def abstract_preview_size(paper):
    print(paper.preview_image)
    return 420 if paper.preview_image else 900
