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

        papers_count = papers.count()

        if not papers_count or papers_count == 0:
            self.log("No new papers to categorize")
        else:
            self.log("Categorizing", papers.count(), "papers")

            for paper, result in self.progress(classifier.prediction_iterator(papers), length=papers.count()):

                found_matching_category = False

                for category, score in result.items():
                    if score > self._category_threshold:
                        found_matching_category = True
                        paper.categories.add(Category.objects.get(model_identifier=category), through_defaults={
                            'score': (score - self._category_threshold) * 2
                        })
                        paper.save(set_manually_modified=False)

                if not found_matching_category:
                    best_matching_category, score = max(result.items(), key=lambda x: x[1])

                    self.log("Found paper", paper.doi, "with no good matching category. Assigned it to",
                             best_matching_category, "where it has score", score)

                    paper.categories.add(Category.objects.get(model_identifier=best_matching_category), through_defaults={
                        'score': 0
                    })
                    paper.save(set_manually_modified=False)

        self.log("Finished updating category assignment")
