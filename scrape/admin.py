from django.contrib import admin
from .citation_refresher import CitationRefresher
from data.models import Paper, Topic, PaperHost, Author
from django.urls import path
from django.http import HttpResponseRedirect

admin.site.register(Topic)
admin.site.register(PaperHost)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    change_list_template = "scrape/author_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('citations/', self.refresh_citations),
        ]
        return my_urls + urls

    def refresh_citations(self, request):
        citation_refresher = CitationRefresher()
        citation_refresher.refresh_citations()
        self.message_user(request, "All citations inserted")
        return HttpResponseRedirect("../")

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    change_list_template = "scrape/paper_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('update_papers/', self.refresh_papers),
            path('update_images/', self.refresh_images),
        ]
        return my_urls + urls

    def refresh_papers(self, request):
        # todo
        self.message_user(request, "Papers updated")
        return HttpResponseRedirect("../")

    def refresh_images(self, request):
        # todo
        self.message_user(request, "PDF thumbnails updated")
        return HttpResponseRedirect("../")