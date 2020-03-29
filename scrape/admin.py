from django.contrib import admin
from .citation_refresher import CitationRefresher
from data.models import Paper, Topic, PaperHost, Author
from django.urls import path
from django.http import HttpResponseRedirect

from .pdf_image_scraper import PdfImageScraper
from .scrape_articles import scrape_articles

admin.site.register(Topic)
admin.site.register(PaperHost)

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    change_list_template = "scrape/author_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('update_citations/', self.refresh_citations),
            path('get_new_citations/', self.get_new_citations),
        ]
        return my_urls + urls

    def refresh_citations(self, request):
        citation_refresher = CitationRefresher()
        if citation_refresher.refresh_citations(count=100):
            self.message_user(request, "100 oldest citations updated")
        else:
            self.message_user(request, "Error while scraping Google Scholar Citations")
        return HttpResponseRedirect("../")

    def get_new_citations(self, request):
        citation_refresher = CitationRefresher()
        if citation_refresher.refresh_citations(only_new=True):
            self.message_user(request, self.message_user(request, "All new citations inserted"))
        else:
            self.message_user(request, "Error while scraping Google Scholar Citations")
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
        scrape_articles()
        self.message_user(request, "Papers updated")
        return HttpResponseRedirect("../")

    def refresh_images(self, request):
        image_scraper = PdfImageScraper()
        image_scraper.load_images()
        self.message_user(request, "PDF thumbnails updated")
        return HttpResponseRedirect("../")