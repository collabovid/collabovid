from src.analyze.vectorizer.exceptions import *


class SemanticPaperSearch:
    def query(self, query: str):
        raise NotImplementedError("query not implemented")

    def is_ready(self):
        return True


class EmbeddingSemanticPaperSearch:
    def __init__(self, vectorizer):
        self._vectorizer = vectorizer

    def query(self, query: str):
        indices, scores = self._vectorizer.matching_to_query(query)
        return list(zip(indices, scores))

    def is_ready(self):
        try:
            _ = self._vectorizer.paper_matrix
        except CouldNotLoadPaperMatrix as e:
            print(e)
            return False
        return self._vectorizer.models_initialized()
