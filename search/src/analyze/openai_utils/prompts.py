import json


class TopicsPrompt:

    def __init__(self, topic_name=None, titles=None, abstracts=None):
        self._topic_name = topic_name
        self._titles = titles
        self._abstracts = titles

    @staticmethod
    def clean_text(title):
        return title.replace("\n", "")

    @staticmethod
    def combine_representations(first, second):
        first = str(first) + "\n\n\n" if first else ""
        return first + str(second)

    @staticmethod
    def get_topic_representation(titles, abstracts=None, topic_name=None):
        prompt = ""

        if abstracts:
            for title, abstract in zip(titles, abstracts):
                prompt += "Title: " + TopicsPrompt.clean_text(title) + "\nAbstract: " + TopicsPrompt.clean_text(
                    abstract) + "\n"
        else:
            for title in titles:
                prompt += TopicsPrompt.clean_text(title) + "\n"

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

        self._topic_names = [entry["name"] for entry in self._examples]
        self._titles = [entry["titles"] for entry in self._examples]
        self._abstracts = [entry["abstracts"] if "abstracts" in entry else None for entry in self._examples]

    def __repr__(self):
        prompt = None
        for topic_name, titles, abstracts in zip(self._topic_names, self._titles, self._abstracts):
            prompt = self.combine_representations(prompt,
                                                  self.get_topic_representation(titles=titles, abstracts=abstracts,
                                                                                topic_name=topic_name))

        return prompt
