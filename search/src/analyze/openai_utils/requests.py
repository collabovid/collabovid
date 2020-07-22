from src.analyze.openai_utils.prompts import *
from data.models import Topic, TopicNameSuggestion, Paper

from collections import defaultdict
from math import ceil
import json
from collections import defaultdict
import openai
import time

class SuggestionCalculator:

    def __init__(self, example, n):
        self._example = example
        self._n = n

    def topic_name_request(self, topics_prompt):
        prompt = TopicsPrompt.combine_representations(self._example, topics_prompt)

        response = None

        while not response:
            try:
                response = openai.Completion.create(engine="davinci", prompt=prompt, n=self._n, top_p=0.2, stop="\n\n\n")
            except openai.error.APIError:
                print("Got API Error")
                time.sleep(5)

        for choice in response["choices"]:
            if choice["finish_reason"] != "stop":
                pass
                # print("Unexpected finish reason", choice)

            yield choice["text"].strip()

class TopicNameSuggestionCalculator(SuggestionCalculator):

    def __init__(self, topic: Topic, example, chunk_size=2):
        super(TopicNameSuggestionCalculator, self).__init__(example, n=3)
        self._topic = topic
        self._labels = defaultdict(int)
        self._chunk_size = chunk_size

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


class PaperTopicSuggestionCalculator(SuggestionCalculator):

    def __init__(self, paper: Paper, example):
        super(PaperTopicSuggestionCalculator, self).__init__(example, n=10)
        self._paper = paper
        self._labels = defaultdict(int)

    def suggest_topic(self):

        topics_prompt = TopicsPrompt(
            titles=[self._paper.title], abstracts=[self._paper.abstract])

        for choice in self.topic_name_request(topics_prompt):
            self._labels[choice] += 1

        label_list = sorted([(suggestion, score) for suggestion, score in self._labels.items()],
                            key=lambda x: x[1], reverse=True)

        return label_list[0]
