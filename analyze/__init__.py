from .vectorizer import PretrainedCountVectorizer
from .topic_scorer import PretrainedLDA
from scipy.spatial.distance import jensenshannon
import os
import numpy as np
from data.models import Paper, Topic
import joblib
import heapq
from tqdm import tqdm

paper_matrix = joblib.load('res/paper_matrix.pkl')
dir_path = os.path.dirname(os.path.realpath(__file__))
vectorizer = PretrainedCountVectorizer(os.path.join(dir_path, 'res/vectorizer.pkl'))
topic_scorer = PretrainedLDA(os.path.join(dir_path, 'res/lda.pkl'), vectorizer)


def compute_topic_score(texts):
    scores = topic_scorer.score(texts)
    return scores


def doc_similarity(doc_dist1, doc_dist2):
    return 1 - jensenshannon(doc_dist1, doc_dist2)


def doc_similarities(doc_topic_distributions, doc_dist):
    return np.apply_along_axis(lambda x: doc_similarity(x, doc_dist), 1, doc_topic_distributions)


def calculate_paper_matrix():
    paper = Paper.objects.all()
    texts = [p.abstract for p in paper]
    matrix = compute_topic_score(texts)
    id_map = {}
    for index, p in enumerate(paper):
        id_map[p.doi] = index

    paper_matrix = {
        'id_map': id_map,
        'index_arr': [p.doi for p in paper],
        'matrix': matrix
    }
    joblib.dump(paper_matrix, 'res/paper_matrix.pkl')


def assign_to_topics():
    topics = Topic.objects.all()
    descriptions = [topic.description for topic in topics]
    latent_topic_scores = compute_topic_score(descriptions)
    paper = Paper.objects.all()
    matrix = paper_matrix['matrix']
    for p in tqdm(paper):
        arr_index = paper_matrix['id_map'][p.doi]
        similarities = doc_similarities(latent_topic_scores, matrix[arr_index])
        most_similar_idx = np.argmax(similarities).item()
        p.topic = topics[most_similar_idx]
        p.topic_score = similarities[most_similar_idx]
        p.save()
    for topic in topics:
        topic.save()


def related(query, top=20):
    query_dist = compute_topic_score([query])[0]
    matrix = paper_matrix['matrix']
    similarity_scores = doc_similarities(matrix, query_dist)
    related_papers = zip(paper_matrix['index_arr'], similarity_scores)
    related_papers = heapq.nlargest(top, related_papers, key=lambda x: x[1])
    return [(Paper.objects.get(pk=p[0]), p[1]) for p in related_papers]
