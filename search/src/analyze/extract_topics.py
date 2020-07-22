from data.models import Paper, Topic

import os
from tasks.definitions import Runnable, register_task
from django.conf import settings
from src.analyze.openai_utils.prompts import *
from src.analyze.openai_utils.requests import PaperTopicSuggestionCalculator


@register_task
class ExtractTopics(Runnable):

    @staticmethod
    def task_name():
        return "extract-topics"

    def __init__(self, *args, **kwargs):
        super(ExtractTopics, self).__init__(*args, **kwargs)

    def run(self):
        self.log("Topic extraction started")

        examples_prompt = FileTopic(file_name=os.path.join(settings.BASE_DIR, "resources/topic_sample.json"))

        Topic.objects.all().delete()

        for paper in self.progress(Paper.objects.all()[:5000]):
            self.log("Calculating suggestions for", paper.title)

            paper_topic_suggestion_calculator = PaperTopicSuggestionCalculator(paper=paper, example=examples_prompt)

            topic_suggestions = paper_topic_suggestion_calculator.suggest_topic()

            topic, _ = Topic.objects.get_or_create(name=topic_suggestions[0].lower())
            paper.topic = topic
            paper.save()

            self.log("Suggesting", topic_suggestions)

        self.log("Topic extraction finished")
