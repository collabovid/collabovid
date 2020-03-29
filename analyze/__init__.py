from .vectorizer import PretrainedLDA
from .similarity import JensonShannonSimilarity, CosineDistance
import os
import numpy as np
from data.models import Paper, Topic
import joblib
import heapq
from tqdm import tqdm

dir_path = os.path.dirname(os.path.realpath(__file__))


class PaperAnalyzer():

    def __init__(self, type='lda'):
        if type == 'lda':
            self.vectorizer = PretrainedLDA(os.path.join(dir_path, 'res/lda.pkl'),
                                            os.path.join(dir_path, 'res/vectorizer.pkl'))
            self.similarity_computer = JensonShannonSimilarity()
        elif type == 'biobert':
            from .bert_vectorizer import BioBertVectorizer
            self.vectorizer = BioBertVectorizer()
            self.similarity_computer = CosineDistance()
        else:
            raise ValueError('Unknown type')

        self.paper_matrix = None
        matrix_path = os.path.join(dir_path, 'res/paper_matrix.pkl')
        if os.path.exists(matrix_path):
            self.paper_matrix = joblib.load(matrix_path)

    def calculate_paper_matrix(self):
        paper = Paper.objects.all()
        texts = [p.abstract for p in paper]
        matrix = self.vectorizer.vectorize(texts)
        id_map = {}
        for index, p in enumerate(paper):
            id_map[p.doi] = index

        self.paper_matrix = {
            'id_map': id_map,
            'index_arr': [p.doi for p in paper],
            'matrix': matrix
        }
        joblib.dump(self.paper_matrix, 'res/paper_matrix.pkl')

    def assign_to_topics(self):
        if self.paper_matrix is None:
            raise
        topics = Topic.objects.all()
        descriptions = [topic.description for topic in topics]
        latent_topic_scores = self.vectorizer.vectorize(descriptions)
        paper = Paper.objects.all()
        matrix = self.paper_matrix['matrix']
        for p in tqdm(paper):
            arr_index = self.paper_matrix['id_map'][p.doi]
            similarities = self.similarity_computer.similarities(latent_topic_scores, matrix[arr_index])
            most_similar_idx = np.argmax(similarities).item()
            p.topic = topics[most_similar_idx]
            p.topic_score = similarities[most_similar_idx]
            p.save()
        for topic in topics:
            topic.save()

    def related(self, query, top=20):
        query_dist = self.vectorizer.vectorize([query])[0]
        matrix = self.paper_matrix['matrix']
        similarity_scores = self.similarity_computer.similarities(matrix, query_dist)
        related_papers = zip(self.paper_matrix['index_arr'], similarity_scores)
        related_papers = heapq.nlargest(top, related_papers, key=lambda x: x[1])
        return [(Paper.objects.get(pk=p[0]), p[1]) for p in related_papers]
