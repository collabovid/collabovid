from .vectorizer import PretrainedLDA
from .similarity import JensonShannonSimilarity, CosineDistance
import os
from src.analyze.analyzer import CombinedPaperAnalyzer, BasicPaperAnalyzer
from src.analyze.vectorizer.exceptions import *

dir_path = os.path.dirname(os.path.realpath(__file__))

analyzer = None
topic_assignment_analyzer = None

analyzer_currently_initializing = False


def is_analyzer_initialized():
    global analyzer
    return analyzer is not None


def is_analyzer_initializing():
    global analyzer_currently_initializing
    return analyzer_currently_initializing


def get_topic_assignment_analyzer():
    global topic_assignment_analyzer

    if not topic_assignment_analyzer:

        try:
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
        except (CouldNotLoadModel, CouldNotLoadVectorizer, CouldNotLoadPaperMatrix) as e:
            topic_assignment_analyzer = None
            raise e

    return topic_assignment_analyzer


def get_analyzer():
    global analyzer, analyzer_currently_initializing

    if not analyzer and not analyzer_currently_initializing:
        analyzer_currently_initializing = True

        try:
            print("Initializing Paper Analyzer")
            analyzer = BasicPaperAnalyzer('sentence-transformer')
        except (CouldNotLoadModel, CouldNotLoadVectorizer, CouldNotLoadPaperMatrix) as e:
            print(e)
            analyzer = None

        analyzer_currently_initializing = False

    return analyzer
