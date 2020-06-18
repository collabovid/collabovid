from tasks.definitions import Runnable, register_task
from . import get_vectorizer, get_used_vectorizers
import time


def wait_until(condition, interval=0.1, timeout=10):
    start = time.time()
    while not condition() and time.time() - start < timeout:
        time.sleep(interval)
    return condition()


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
        if self._vectorizer is not None and self._vectorizer.strip() != "":
            vectorizer_names.append(self._vectorizer)
        else:
            vectorizer_names = get_used_vectorizers()

        for vectorizer_name in vectorizer_names:
            print(f'Preprocessing {vectorizer_name}')
            vectorizer = get_vectorizer(vectorizer_name)

            model_loaded = True
            if not vectorizer.models_initialized():
                if not vectorizer.initializing_models():
                    model_loaded = False
                    vectorizer.initialize_models()
                else:
                    # wait 120s until models are initialized
                    success = wait_until(vectorizer.models_initialized, timeout=120)
                    if not success:
                        raise RuntimeError("Could not load models")

            vectorizer.preprocess(force_recompute=self._force_recompute)

            # cleanup models
            if not model_loaded:
                vectorizer.cleanup_models()

        self.log("Preprocessing finished")
