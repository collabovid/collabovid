import heapq
from src.analyze.vectorizer.exceptions import *


class SimilarPaperFinder:
    def similar(self, doi: str, top: int = None):
        raise NotImplementedError("similar not implemented")

    def is_ready(self):
        return True


class EmbeddingSimilarPaperFinder(SimilarPaperFinder):
    def __init__(self, vectorizer):
        self._vectorizer = vectorizer

    def similar(self, doi: str, top: int = None):
        indices, scores = self._vectorizer.similar_to_paper(doi)
        results = list(zip(indices, scores))
        if top is None:
            top = len(results) - 1
        results = heapq.nlargest(top, results, key=lambda x: x[1])
        return results

    def is_ready(self):
        try:
            _ = self._vectorizer.paper_matrix
        except CouldNotLoadPaperMatrix as e:
            print(e)
            return False
        return True
