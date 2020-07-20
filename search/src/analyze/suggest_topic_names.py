import openai
from django.db.models import QuerySet

from data.models import Topic, TopicNameSuggestion

from collections import defaultdict
from math import ceil
import json
import os
from tasks.definitions import Runnable, register_task
from django.conf import settings


class TopicsPrompt:

    def __init__(self, topic_name=None, titles=None):
        self._topic_name = topic_name
        self._titles = titles

    @staticmethod
    def clean_title(title):
        return title.replace("\n", "")

    @staticmethod
    def combine_representations(first, second):
        first = str(first) + "\n\n\n" if first else ""
        return first + str(second)

    @staticmethod
    def get_topic_representation(titles, topic_name=None):
        prompt = ""

        for title in titles:
            prompt += TopicsPrompt.clean_title(title) + "\n"

        prompt += "\nTopic:"

        if topic_name:
            prompt += " " + topic_name

        return prompt

    def __repr__(self):

        if not self._titles:
            raise ValueError()

        return self.get_topic_representation(self._titles, self._topic_name)


class FileTopic(TopicsPrompt):

    def __init__(self, file_name):
        super(FileTopic, self).__init__()

        with open(file_name, 'r') as f:
            self._examples = json.load(f)

        topic_names = [entry["name"] for entry in self._examples]
        titles = [entry["titles"] for entry in self._examples]

        self._topic_names = topic_names
        self._titles = titles

    def __repr__(self):
        prompt = None
        for topic_name, titles in zip(self._topic_names, self._titles):
            prompt = self.combine_representations(prompt, self.get_topic_representation(titles, topic_name))

        return prompt


class TopicNameSuggestionCalculator:

    def __init__(self, topic: Topic, example, chunk_size=2):
        self._topic = topic
        self._labels = defaultdict(int)
        self._chunk_size = chunk_size
        self._example = example

    def topic_name_request(self, topics_prompt):
        prompt = TopicsPrompt.combine_representations(self._example, topics_prompt)
        response = openai.Completion.create(engine="davinci", prompt=prompt, n=3, top_p=0.2, stop="\n\n\n")
        for choice in response["choices"]:
            if choice["finish_reason"] != "stop":
                pass
                # print("Unexpected finish reason", choice)

            yield choice["text"].strip()

    def suggest_names(self):
        papers = self._topic.papers.all()
        total = papers.count()

        for i in range(ceil(total / self._chunk_size)):
            topics_prompt = TopicsPrompt(
                titles=[paper.title for paper in papers[i * self._chunk_size:(i + 1) * self._chunk_size]])

            for choice in self.topic_name_request(topics_prompt):
                self._labels[choice] += 1

        label_list = sorted([(suggestion, score) for suggestion, score in self._labels.items()],
                            key=lambda x: x[1], reverse=True)

        return label_list


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
