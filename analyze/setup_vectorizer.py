from tasks import Runnable, register_task
from . import get_topic_assignment_analyzer, get_analyzer
from analyze.analyzer import PaperAnalyzer


@register_task
class SetupVectorizer(Runnable):

    @staticmethod
    def task_name():
        return "setup-vectorizer"

    def __init__(self, analyzer: PaperAnalyzer = None, *args, **kwargs):
        super(SetupVectorizer, self).__init__(*args, **kwargs)
        self.analyzer = analyzer

    def run(self):

        self.log("Preprocessing started")

        if self.analyzer:
            self.log("Preprocess of given analyzer")
            self.analyzer.preprocess()
        else:
            self.log("Preprocess of analyzer and topic analyzer")
            analyzer = get_analyzer()
            analyzer.preprocess()

            topic_analyzer = get_topic_assignment_analyzer()
            topic_analyzer.preprocess()

        self.log("Preprocessing finished")