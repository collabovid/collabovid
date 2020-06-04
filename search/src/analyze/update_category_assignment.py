from tasks.definitions import Runnable, register_task
from src.analyze.models.litcovid_classifier import LitcovidMultiLabelClassifier
from data.models import Paper, Category

from django.conf import settings
import os


@register_task
class UpdateCategoryAssignment(Runnable):

    @staticmethod
    def task_name():
        return "update-category-assignment"

    def __init__(self, force_recompute: bool = False, category_threshold: float = 0.5, *args, **kwargs):
        super(UpdateCategoryAssignment, self).__init__(*args, **kwargs)
        self._force_recompute = force_recompute
        self._category_threshold = category_threshold

    def run(self):
        self.log("Updating category assignment")
        self.log("Assigning papers to categories...")

        self.log("Loading classifier")
        classifier = LitcovidMultiLabelClassifier(os.path.join(settings.MODELS_BASE_DIR, "litcovid_longformer_base"),
                                                  device='cpu')
        self.log("Loaded classifier. Retrieving papers...")

        if self._force_recompute:
            papers = Paper.objects.all()
        else:
            papers = Paper.objects.filter(categories=None)

        self.log("Categorizing", papers.count(), "papers")

        for paper, result in classifier.prediction_iterator(papers):
            for category, score in result.items():
                if score > self._category_threshold:
                    paper.categories.add(Category.objects.get(model_identifier=category), through_defaults={
                        'score': (score-self._category_threshold) * 2
                    })
                    paper.save()

        self.log("Finished updating category assignment")
