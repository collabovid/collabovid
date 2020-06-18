import os
from src.analyze.analyzer import EmbeddingSimilarPaperFinder, EmbeddingSemanticPaperSearch
from src.analyze.vectorizer.exceptions import *
from src.analyze.vectorizer import get_vectorizer
from threading import Thread

SEARCH_VECTORIZER = 'title-sentence'
SIMILAR_VECTORIZER = 'transformer-paper-oubiobert-512'

dir_path = os.path.dirname(os.path.realpath(__file__))
semantic_paper_search = None
similar_paper_finder = None


def get_used_vectorizers():
    names = list({SEARCH_VECTORIZER, SIMILAR_VECTORIZER})
    return names


def get_semantic_paper_search():
    global semantic_paper_search
    if not semantic_paper_search:
        try:
            vectorizer = get_vectorizer(SEARCH_VECTORIZER)
            semantic_paper_search = EmbeddingSemanticPaperSearch(vectorizer)
            thread = Thread(target=vectorizer.initialize_models)
            thread.start()
        except (CouldNotLoadModel, CouldNotLoadVectorizer, CouldNotLoadPaperMatrix) as e:
            print(e)
            semantic_paper_search = None
    return semantic_paper_search


def get_similar_paper_finder():
    global similar_paper_finder
    if not similar_paper_finder:
        try:
            vectorizer = get_vectorizer(SIMILAR_VECTORIZER)
            similar_paper_finder = EmbeddingSimilarPaperFinder(vectorizer)
        except (CouldNotLoadPaperMatrix) as e:
            print(e)
            similar_paper_finder = None
    return similar_paper_finder
