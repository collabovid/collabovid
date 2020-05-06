from django.db import models
from django.utils.crypto import get_random_string
from data.models import Paper

def generate_token():
    return get_random_string(length=64)


class Token(models.Model):
    token = models.CharField(max_length=64, primary_key=True, default=generate_token)


class Category(models.Model):
    text = models.TextField()


class Subcategory(models.Model):
    parent = models.ForeignKey(Category, related_name="sub_categories", on_delete=models.CASCADE)
    text = models.TextField()


class Classification(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name="classifications")
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)

    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE,
                                 related_name="classifications",
                                 null=True, default=None)
    sub_category = models.ForeignKey(Subcategory,
                                     on_delete=models.CASCADE,
                                     related_name="classifications",
                                     null=True, default=None)


