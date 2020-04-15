from django.contrib import admin
from .models import Token, Category, Subcategory, Classification
admin.site.register(Token)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Classification)
