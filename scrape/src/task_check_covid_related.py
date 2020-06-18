from data.models import Paper
from src.static_functions import covid_related
from tasks.definitions import register_task, Runnable


@register_task
class CheckCovidRelatedTask(Runnable):
    @staticmethod
    def task_name():
        return "check-covid-related"

    def __init__(self, *args, **kwargs):
        super(CheckCovidRelatedTask, self).__init__(*args, **kwargs)

    def run(self):
        self.log("Check which papers are related to COVID-19")
        for paper in self.progress(Paper.objects.all()):
            paper.covid_related = covid_related(paper)
            paper.save()
