from .vectorizer import PretrainedLDA
from .similarity import JensonShannonSimilarity, CosineDistance
import os
from src.analyze.analyzer import CombinedPaperAnalyzer, BasicPaperAnalyzer

dir_path = os.path.dirname(os.path.realpath(__file__))

analyzer = None
topic_assignment_analyzer = None


def get_topic_assignment_analyzer():
    global topic_assignment_analyzer

    if not topic_assignment_analyzer:
        topic_assignment_analyzer = CombinedPaperAnalyzer(
            {
                "lda":
                    {
                        "analyzer": BasicPaperAnalyzer('lda'),
                        "weight": .5
                    },
                "title_sentence":
                    {
                        "analyzer": get_analyzer(),
                        "weight": .5
                    }
            }
        )

    return topic_assignment_analyzer


def get_analyzer():
    global analyzer

    if not analyzer:
        print("Initializing Paper Analyzer")

        analyzer = BasicPaperAnalyzer('sentence-transformer')

    return analyzer
