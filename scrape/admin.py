from django.contrib import admin
from data.models import Paper, Topic, PaperHost, Author
from django.urls import path
from django.http import HttpResponseRedirect
from .scrape import Scrape

from django.core.management import call_command

from tasks.task_runner import TaskRunner

admin.site.register(Topic)
admin.site.register(PaperHost)
admin.site.register(Author)


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
        self.message_user(request, "Paper update initiated")
        return HttpResponseRedirect("../")

    def loaddata(self, request):
        fixture = request.POST.get("fixture")
        call_command('loaddata', fixture)

        self.message_user(request, "Loaded fixture")
        return HttpResponseRedirect("../")
