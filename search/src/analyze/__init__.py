import os
from src.analyze.analyzer import BasicPaperAnalyzer
from src.analyze.vectorizer.exceptions import *

dir_path = os.path.dirname(os.path.realpath(__file__))

analyzer = None
similarity_analyzer = None
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


def get_similarity_analyzer():
    global similarity_analyzer

    if not similarity_analyzer:
        try:
            print('initializing similarity')
            similarity_analyzer = BasicPaperAnalyzer('transformer-paper')
        except (CouldNotLoadModel, CouldNotLoadVectorizer, CouldNotLoadPaperMatrix) as e:
            print(e)
            similarity_analyzer = None
        print('finished')
    return similarity_analyzer
