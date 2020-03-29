from scipy.spatial.distance import jensenshannon
import numpy as np


class SimilarityComputer():
    def similiarities(self, vectors, vec):
        raise NotImplementedError


class JensonShannonSimilarity(SimilarityComputer):
    def similarities(self, vectors, vec):
        return np.apply_along_axis(lambda x: 1 - jensenshannon(x, vec), 1, vectors)


class CosineDistance(SimilarityComputer):
    def similiarities(self, vectors, vec):
        pass
