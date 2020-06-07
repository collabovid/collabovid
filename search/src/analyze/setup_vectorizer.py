from tasks.definitions import Runnable, register_task
from . import get_analyzer
from src.analyze.analyzer import PaperAnalyzer


@register_task
class SetupVectorizer(Runnable):

    @staticmethod
    def task_name():
        return "setup-vectorizer"

    def __init__(self, analyzer: PaperAnalyzer = None, force_recompute: bool = False, *args, **kwargs):
        super(SetupVectorizer, self).__init__(*args, **kwargs)
        self.analyzer = analyzer
        self._force_recompute = force_recompute

    def run(self):

        self.log("Preprocessing started")

        if self._force_recompute:
            self.log("Forcing recompute on the analyzers")

        if self.analyzer:
            self.log("Preprocess of given analyzer")
            self.analyzer.preprocess(force_recompute=self._force_recompute)
        else:
            self.log("Preprocess of analyzer")

            analyzer = get_analyzer()
            analyzer.preprocess(force_recompute=self._force_recompute)

        self.log("Preprocessing finished")