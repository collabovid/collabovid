from django.db import models
from django.templatetags.static import static

class PaperHost(models.Model):
    """
    e.g. medrxiv
    """
    name = models.CharField(max_length=60)
    url = models.URLField()


class Author(models.Model):
    """
    TODO: Add Google Scholar, ORCID etc.
    """
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)


class Category(models.Model):
    """
    e.g. Microbiology
    """
    name = models.CharField(max_length=60, primary_key=True)


class Paper(models.Model):
    doi = models.CharField(max_length=100, primary_key=True)

    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, related_name="publications")
    category = models.ForeignKey(Category, related_name="papers", on_delete=models.CASCADE)
    host = models.ForeignKey(PaperHost, related_name="papers", on_delete=models.CASCADE)

    abstract = models.TextField()

    url = models.URLField()
    is_preprint = models.BooleanField(default=True)

    published_at = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
