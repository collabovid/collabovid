import openai
from django.db.models import QuerySet

from data.models import Topic, TopicNameSuggestion

import os
from tasks.definitions import Runnable, register_task
from django.conf import settings
from src.analyze.openai_utils.prompts import *
from src.analyze.openai_utils.requests import TopicNameSuggestionCalculator


@register_task
class SuggestTopicNames(Runnable):

    @staticmethod
    def task_name():
        return "suggest-topic-names"

    def __init__(self, topic_pk: int = -1, topics: QuerySet = None, *args, **kwargs):
        super(SuggestTopicNames, self).__init__(*args, **kwargs)

        if topic_pk >= 0:
            self._topics = Topic.objects.filter(pk=topic_pk)
        elif topics:
            self._topics = topics
        else:
            ValueError("No topic provided")

    def run(self):
        self.log("Name suggestion started")

        examples_prompt = FileTopic(file_name=os.path.join(settings.BASE_DIR, "resources/topic_sample.json"))

        for topic in self.progress(self._topics):
            self.log("Calculating suggestions for", topic.name)

            topic_name_suggestion_calculator = TopicNameSuggestionCalculator(topic=topic, example=examples_prompt)

            for suggestion, score in topic_name_suggestion_calculator.suggest_names():
                TopicNameSuggestion.objects.create(topic=topic, name=suggestion, score=score)

        self.log("Name suggestions finished")
