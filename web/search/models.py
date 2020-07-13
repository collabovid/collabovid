from django.db import models
from django.contrib.postgres.fields import JSONField


class SearchQuery(models.Model):
    query = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
