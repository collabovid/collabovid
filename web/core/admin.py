from django.contrib import admin
from data.models import Category, Paper, Topic, PaperHost, Author

admin.site.register(Category)
admin.site.register(Paper)
admin.site.register(Topic)
admin.site.register(PaperHost)
admin.site.register(Author)
