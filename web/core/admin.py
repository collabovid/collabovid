from django.contrib import admin
from data.models import Category, Paper, Topic, PaperHost, Author, Journal, GeoCity, GeoCountry, GeoNameResolution

admin.site.register(Category)
admin.site.register(Paper)
admin.site.register(Topic)
admin.site.register(PaperHost)
admin.site.register(Author)
admin.site.register(Journal)
admin.site.register(GeoCity)
admin.site.register(GeoCountry)
admin.site.register(GeoNameResolution)
