from django.contrib import admin
from data.models import Category, Paper, Topic, PaperHost, Author, Journal, GeoCity, GeoCountry, GeoNameResolution, \
    IgnoredPaper

admin.site.register(Category)
admin.site.register(Topic)
admin.site.register(PaperHost)
admin.site.register(Author)
admin.site.register(Journal)
admin.site.register(GeoCity)
admin.site.register(GeoCountry)
admin.site.register(GeoNameResolution)
admin.site.register(IgnoredPaper)


class PaperAdmin(admin.ModelAdmin):
    exclude = ('data',)

    actions = ['delete_model']

    def delete_queryset(self, request, queryset):
        for paper in queryset:
            IgnoredPaper.objects.get_or_create(doi=paper.doi)
        super(PaperAdmin, self).delete_queryset(request, queryset)

    def delete_model(self, request, obj):
        IgnoredPaper.objects.get_or_create(doi=obj.doi)
        super(PaperAdmin, self).delete_model(request, obj)

    def save_model(self, request, obj, form, change):
        obj.manually_modified = True
        super(PaperAdmin, self).save_model(request, obj, form, change)


admin.site.register(Paper, PaperAdmin)
