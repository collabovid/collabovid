from scipy.spatial.distance import jensenshannon
import numpy as np
import scipy.spatial.distance as dist


class SimilarityComputer():
    def similiarities(self, vectors, vec):
        raise NotImplementedError


class JensonShannonSimilarity(SimilarityComputer):
    def similarities(self, vectors, vec):
        return np.apply_along_axis(lambda x: 1 - jensenshannon(x, vec), 1, vectors)


class CosineDistance(SimilarityComputer):
    def similarities(self, vectors, vec):
        scores = (2 - dist.cdist(vectors, np.array([vec]), metric='cosine')) / 2
        return [score.item() for score in scores]
