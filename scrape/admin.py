from django.contrib import admin
from .citation_refresher import CitationRefresher
from data.models import Paper, Topic, PaperHost, Author
from django.urls import path
from django.http import HttpResponseRedirect

from .pdf_image_scraper import PdfImageScraper
from .scrape_articles import scrape_articles
from setup.image_downloader import run as run_image_downloader
from setup.lda_setup import run as run_lda_setup
from setup.image_s3_apply import run as run_s3_apply

from django.core.management import call_command

admin.site.register(Topic)
admin.site.register(PaperHost)


class Container:
    def __init__(self, data):
        self.data = data

    def append(self, extra):
        self.data += extra

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
            path('setup_pdf_images/', self.setup_pdf_images),
            path('load_data_from_fixture/', self.loaddata),
            path('setup_lda/', self.setup_lda),
            path('setup_s3_apply/', self.setup_s3_apply),
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

    def loaddata(self, request):
        fixture = request.POST.get("fixture")
        call_command('loaddata', fixture)

        self.message_user(request, "Loaded fixture")
        return HttpResponseRedirect("../")

    def setup_pdf_images(self, request):
        container = Container("")

        def output(output, container=container):
            container.append(str(output) + "\n")

        run_image_downloader(output)

        self.message_user(request, self.message_user(request, container.data))
        return HttpResponseRedirect("../")

    def setup_lda(self, request):
        container = Container("")

        def output(*args, container=container):
            output = " ".join(list(args))
            container.append(str(output) + "\n")

        run_lda_setup(output)

        self.message_user(request, self.message_user(request, container.data))
        return HttpResponseRedirect("../")

    def setup_s3_apply(self, request):
        container = Container("")

        def output(*args, container=container):
            output = " ".join(list(args))

            container.append(str(output) + "\n")

        run_s3_apply(output)

        self.message_user(request, self.message_user(request, container.data))
        return HttpResponseRedirect("../")
