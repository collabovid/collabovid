import os

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'search.settings_dev')
    import django

    django.setup()
    from django.conf import settings
    from src.analyze.models.litcovid_classifier import LitcovidMultiLabelClassifier
    from data.models import Paper

    papers = Paper.objects.all()
    papers_iterator = iter(list(papers[:10]))

    classifier = LitcovidMultiLabelClassifier(os.path.join(settings.MODELS_BASE_DIR, "litcovid_longformer_base"),
                                              device='cpu')
    for paper, result in classifier.prediction_iterator(papers_iterator):
        print(paper.title)
        for category, score in result.items():
            if score > 0.5:
                print(f'{category}: {score}')
