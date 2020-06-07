from .vectorizer import PretrainedLDA
from .similarity import JensonShannonSimilarity, CosineDistance
import os
from src.analyze.analyzer import CombinedPaperAnalyzer, BasicPaperAnalyzer
from src.analyze.vectorizer.exceptions import *

dir_path = os.path.dirname(os.path.realpath(__file__))

analyzer = None
analyzer_currently_initializing = False


def is_analyzer_initialized():
    global analyzer
    return analyzer is not None


def is_analyzer_initializing():
    global analyzer_currently_initializing
    return analyzer_currently_initializing


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
