from django.contrib import admin
from .citation_refresher import CitationRefresher
from data.models import Paper, Topic, PaperHost, Author
from django.urls import path
from django.http import HttpResponseRedirect

from .pdf_image_scraper import PdfImageScraper
from .scrape import Scrape
from setup.image_downloader import run as run_image_downloader
from setup.setup_vectorizers import run as run_vectorizer_setup
from setup.image_s3_apply import run as run_s3_apply

from django.core.management import call_command

from tasks.task_runner import TaskRunner

admin.site.register(Topic)
admin.site.register(PaperHost)

#TODO: Change URL Of LDA

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
        my_urls = []
        return my_urls + urls


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    change_list_template = "scrape/paper_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('update_papers/', self.refresh_papers),
            path('load_data_from_fixture/', self.loaddata),
        ]
        return my_urls + urls

    def refresh_papers(self, request):
        TaskRunner.run_task_async(Scrape)
        self.message_user(request, "Papers updated")
        return HttpResponseRedirect("../")

    def loaddata(self, request):
        fixture = request.POST.get("fixture")
        call_command('loaddata', fixture)

        self.message_user(request, "Loaded fixture")
        return HttpResponseRedirect("../")
