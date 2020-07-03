from data.models import DeleteCandidate, Paper
from src.language_detection.language_detector import LanguageDetector
from tasks.definitions import register_task, Runnable


@register_task
class LanguageDetectionTask(Runnable):
    @staticmethod
    def task_name():
        return 'detect-non-english-papers'

    @staticmethod
    def description():
        return 'Determine papers with titles or abstract not in english'

    def __init__(self, *args, **kwargs):
        super(LanguageDetectionTask, self).__init__(*args, **kwargs)

    def run(self):
        def not_english_prob(result):
            if result.language == 'en' or not result.is_reliable:
                return 0
            return result.probability

        language_detector = LanguageDetector()
        for paper in self.progress(Paper.objects.all()):
            title_lang_prediction = language_detector.detect(paper.title.lower().replace('covid-19', '').replace('sars-cov-2', ''))
            abs_lang_prediction = language_detector.detect(paper.abstract.lower().replace('covid-19', '').replace('sars-cov-2', ''))


            if not_english_prob(title_lang_prediction) > 0 or not_english_prob(abs_lang_prediction) > 0:
                score = 0.5 * (not_english_prob(title_lang_prediction) + not_english_prob(abs_lang_prediction))
                try:
                    DeleteCandidate.objects.get(paper=paper, type=DeleteCandidate.Type.LANGUAGE)
                except DeleteCandidate.DoesNotExist:
                    DeleteCandidate.objects.create(
                        paper=paper, type=DeleteCandidate.Type.LANGUAGE, score=score)
