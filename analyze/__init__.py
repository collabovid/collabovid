from .vectorizer import PretrainedCountVectorizer
from .topic_scorer import PretrainedLDA
from scipy.spatial.distance import jensenshannon
import os
import numpy as np
from data.models import Paper, Topic
import joblib
import heapq

paper_matrix = joblib.load('res/paper_matrix.pkl')


def compute_topic_score(texts):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    vectorizer = PretrainedCountVectorizer(os.path.join(dir_path, 'res/vectorizer.pkl'))
    topic_scorer = PretrainedLDA(os.path.join(dir_path, 'res/lda.pkl'), vectorizer)
    scores = topic_scorer.score(texts)
    return scores


def doc_distance(doc_dist1, doc_dist2):
    return 1 - jensenshannon(doc_dist1, doc_dist2)


def doc_distances(doc_topic_distributions, doc_dist):
    return np.apply_along_axis(lambda x: doc_distance(x, doc_dist), 1, doc_topic_distributions)


def calculate_paper_matrix():
    paper = Paper.objects.all()
    texts = [p.abstract for p in paper]
    print(len(texts))
    matrix = compute_topic_score(texts)
    print(matrix.shape)
    id_map = {}
    for index, p in enumerate(paper):
        id_map[p] = index

    paper_matrix = {
        'id_map': id_map,
        'index_arr': [p.doi for p in paper],
        'matrix': matrix
    }
    joblib.dump(paper_matrix, 'res/paper_matrix.pkl')


def assign_to_topics():
    topics = Topic.objects.all()
    # Todo


def related(query, top=20):
    query_dist = compute_topic_score([query])[0]
    matrix = paper_matrix['matrix']
    distances = doc_distances(matrix, query_dist)
    related_papers = zip(paper_matrix['index_arr'], distances)
    related_papers = heapq.nlargest(top, related_papers, key=lambda x: x[1])
    return [(Paper.objects.get(pk=p[0]), p[1]) for p in related_papers]
