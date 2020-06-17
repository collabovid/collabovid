from tasks.definitions import Runnable, register_task
from . import get_vectorizer, get_used_vectorizers


@register_task
class SetupVectorizer(Runnable):

    @staticmethod
    def task_name():
        return "setup-vectorizer"

    def __init__(self, vectorizer: str = None, force_recompute: bool = False, *args, **kwargs):
        super(SetupVectorizer, self).__init__(*args, **kwargs)
        self._vectorizer = vectorizer
        self._force_recompute = force_recompute

    def run(self):
        self.log("Preprocessing started")
        vectorizer_names = []
        if self._vectorizer:
            vectorizer_names.append(self._vectorizer)
        else:
            vectorizer_names = get_used_vectorizers()

        for vectorizer in vectorizer_names:
            print(f'Preprocessing {vectorizer}')
            get_vectorizer(vectorizer).preprocess(force_recompute=self._force_recompute)

        self.log("Preprocessing finished")
