from tasks.definitions import Runnable, register_task
from data.models import Paper, Topic
from .utils import get_predictive_words


@register_task
class AssignKeywords(Runnable):

    @staticmethod
    def task_name():
        return "assign-keywords"

    @staticmethod
    def description():
        return "Assigns the most predictive keywords to the topics"

    def __init__(self, *args, **kwargs):
        super(AssignKeywords, self).__init__(*args, **kwargs)

    def run(self):
        self.log("Starting AssignKeywords")

        titles_list = []
        topics = list(Topic.objects.all())

        for topic in Topic.objects.all():
            titles = []
            for paper in topic.papers.all():
                titles.append(paper.title)
            titles_list.append(titles)

        top_words = get_predictive_words(titles_list, top=50)
        for topic, words in zip(topics, top_words):
            topic.keywords = ', '.join(words)
            topic.save()

        print('AssignKeywords Finished')
