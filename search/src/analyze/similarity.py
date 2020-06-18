from scipy.spatial.distance import jensenshannon
import numpy as np
import scipy.spatial.distance as dist


class SimilarityComputer():
    def similarities(self, vectors, vec):
        raise NotImplementedError


class JensonShannonSimilarity(SimilarityComputer):
    def similarities(self, vectors, vec):
        return np.apply_along_axis(lambda x: 1 - jensenshannon(x, vec), 1, vectors)


class CosineSimilarity(SimilarityComputer):
    def similarities(self, vectors, vec):
        scores = (2 - dist.cdist(vectors, np.array([vec]), metric='cosine')) / 2
        return [score.item() for score in scores]


class EuclideanSimilarity(SimilarityComputer):
    def similarities(self, vectors, vec):
        scores = 1 - dist.cdist(vectors, np.array([vec]), metric='euclidean')
        return scores[:,0]
