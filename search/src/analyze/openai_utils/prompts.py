import json
import random as rd

class PaperPrompt:

    def __init__(self, title, topic, topic_index, incorrect_topics=None):
        self._title = title
        self._topic = topic
        self._topic_index = topic_index
        self._incorrect_topics = incorrect_topics

    def append_incorrect_topic(self, topic):
        if self._incorrect_topics is None:
            self._incorrect_topics = list()

        self._incorrect_topics.append(topic)

    def __repr__(self):

        incorrect_topics = ""

        if self._incorrect_topics:
            incorrect_topics = "\n".join(
                [f"Topic: {topic}\nError: The topic is not in the category list" for topic in self._incorrect_topics])
            incorrect_topics += "\n"

        return "Title: " + self._title + "\n\n" + incorrect_topics + "Topic:" + (
            f" {self._topic_index}: {self._topic}" if self._topic and self._topic_index else "")


class ClassificationPrompt:

    def __init__(self, file_name):
        with open(file_name, 'r') as f:
            file = json.load(f)

        self._topics = file["topics"]
        self._examples = []
        for example in file["examples"]:
            incorrect_topics = example["incorrect_topics"] if "incorrect_topics" in example else None
            self._examples.append(
                PaperPrompt(title=example["title"],
                            topic=example["topic"],
                            topic_index=self._topics.index(example["topic"]),
                            incorrect_topics=incorrect_topics))

    @property
    def topics(self):
        return self._topics

    def add_topic(self, topic):
        self._topics.append(topic)

    def __repr__(self):
        return "Classify the following titles into one of these categories:\n" + \
               "\n".join([str(i) +": " + topic for i, topic in enumerate(self._topics)]) + \
               "\n\n\n\n" + "\n\n\n".join([str(e) for e in self._examples])


class TopicsPrompt:

    def __init__(self, topic_name=None, titles=None, abstracts=None, suggestions=None):
        self._topic_name = topic_name
        self._titles = titles
        self._abstracts = abstracts
        self._suggestions = suggestions

    @staticmethod
    def clean_text(title):
        return title.replace("\n", "")

    @staticmethod
    def combine_representations(first, second):
        first = str(first) + "\n\n\n" if first else ""
        return first + str(second)

    @staticmethod
    def get_topic_representation(titles, abstracts=None, topic_name=None, suggestions=None):
        prompt = ""

        if abstracts:
            for title, abstract in zip(titles, abstracts):
                prompt += "Title: " + TopicsPrompt.clean_text(title) + "\nAbstract: " + TopicsPrompt.clean_text(
                    abstract) + "\n"
        else:
            for title in titles:
                prompt += TopicsPrompt.clean_text(title) + "\n"

        prompt += "\n"
        prompt += "Suggestions: " + (", ".join(sorted(suggestions)) if suggestions else "") + "\n"
        prompt += "Topic:"

        if topic_name:
            prompt += " " + topic_name

            if suggestions is not None and topic_name not in suggestions:
                prompt += " (new)"

        return prompt

    def __repr__(self):

        if not self._titles:
            raise ValueError()

        return self.get_topic_representation(titles=self._titles,
                                             topic_name=self._topic_name,
                                             abstracts=self._abstracts,
                                             suggestions=self._suggestions)


class FileTopic(TopicsPrompt):

    def __init__(self, file_name):
        super(FileTopic, self).__init__()

        with open(file_name, 'r') as f:
            self._examples = json.load(f)

        self._topic_names = [entry["name"] for entry in self._examples]
        self._titles = [entry["titles"] for entry in self._examples]
        self._abstracts = [entry["abstracts"] if "abstracts" in entry else None for entry in self._examples]
        self._suggestions = list(set(self._topic_names))

        self.initial_suggestions = None

    @property
    def suggestions(self):
        return self._suggestions

    def __repr__(self):
        prompt = None

        if self.initial_suggestions:
            suggestions = self.initial_suggestions
        else:
            suggestions = list()

        for topic_name, titles, abstracts in zip(self._topic_names, self._titles, self._abstracts):
            prompt = self.combine_representations(prompt,
                                                  self.get_topic_representation(titles=titles,
                                                                                abstracts=abstracts,
                                                                                topic_name=topic_name,
                                                                                suggestions=suggestions))

            if topic_name not in suggestions:
                suggestions.append(topic_name)

        return prompt
