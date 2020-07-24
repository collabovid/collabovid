from src.analyze.openai_utils.prompts import *
from data.models import Topic, TopicNameSuggestion, Paper

from collections import defaultdict
from math import ceil
import json
from collections import defaultdict
import openai
import time


class ClassificationCalculator:

    def __init__(self, examples: ClassificationPrompt):

        self._examples = examples
        self._n = 10

        self._labels = defaultdict(int)

    def _request(self, paper_prompt, top_p=0.2):
        response = None
        prompt = str(self._examples) + "\n\n\n" + str(paper_prompt)
        #print(prompt)

        while not response:
            try:
                response = openai.Completion.create(engine="davinci", prompt=prompt, n=self._n, top_p=top_p,
                                                    stop="\n")
            except openai.error.APIError:
                print("Got API Error")
                time.sleep(5)
                continue

        for choice in response["choices"]:
            if choice["finish_reason"] != "stop":
                pass
                # print("Unexpected finish reason", choice)

            yield choice["text"].strip()

    def classify(self, paper):

        paper_prompt = PaperPrompt(title=paper.title, topic_index=None, topic=None)

        top_p = 0.2
        while True:
            for choice in self._request(paper_prompt, top_p=top_p):
                self._labels[choice] += 1

            label_list = sorted([(suggestion, score) for suggestion, score in self._labels.items()],
                                key=lambda x: x[1], reverse=True)

            current_label = label_list[0]

            label, score = current_label
            index, text = label.split(":")
            text = text.strip()
            index = int(index.strip())

            if text in self._examples.topics and self._examples.topics.index(text) == index:
                return (text, score)
            elif top_p < 1:
                paper_prompt.append_incorrect_topic(str(index) + ": " + text)
                self._labels = defaultdict(int)
                top_p = min(top_p+0.1, 1)
            else:
                self._examples.add_topic(text)
                print("adding new category", text)
                return (text, score)


class SuggestionCalculator:

    def __init__(self, example, n):
        self._example = example
        self._n = n

    def topic_name_request(self, topics_prompt):
        prompt = TopicsPrompt.combine_representations(self._example, topics_prompt)
        print(prompt)
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

            cleaned_choice = choice["text"].strip()

            suffix = " (new)"
            if cleaned_choice.endswith(suffix):
                cleaned_choice = cleaned_choice[:-len(suffix)]

            yield cleaned_choice


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

        db_topic_names = list(Topic.objects.all().values_list("name", flat=True))
        topic_names = list(set(self._example._suggestions) | set(db_topic_names))

        print(topic_names)

        self._example.initial_suggestions = db_topic_names

        topics_prompt = TopicsPrompt(
            titles=[self._paper.title], abstracts=[], suggestions=topic_names)

        for choice in self.topic_name_request(topics_prompt):
            self._labels[choice] += 1

        label_list = sorted([(suggestion, score) for suggestion, score in self._labels.items()],
                            key=lambda x: x[1], reverse=True)

        return label_list[0]
