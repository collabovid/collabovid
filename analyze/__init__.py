from .vectorizer import PretrainedLDA
from .similarity import JensonShannonSimilarity, CosineDistance
import os
from .paper_analyzer import CombinedPaperAnalyzer, BasicPaperAnalyzer

dir_path = os.path.dirname(os.path.realpath(__file__))

analyzer = None


def get_analyzer():
    global analyzer

    if not analyzer:
        print("Initializing Paper Analyzer")
        """analyzer = CombinedPaperAnalyzer(
            {
                "lda":
                    {
                        "analyzer": BasicPaperAnalyzer('lda'),
                        "weight": .3
                    },
                "title_sentence":
                    {
                        "analyzer": BasicPaperAnalyzer('sentence-transformer'),
                        "weight": .7
                    }
            }
        )"""
        analyzer = BasicPaperAnalyzer('sentence-transformer')

    return analyzer
