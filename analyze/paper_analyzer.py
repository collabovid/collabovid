from .vectorizer import PretrainedLDA
from .similarity import JensonShannonSimilarity, CosineDistance
import os

import numpy as np
from data.models import Paper, Topic
import joblib
import heapq
from tqdm import tqdm
from django.db import models


class PaperAnalyzer:
    def __init__(self, *args, **kwargs):
        pass

    def calculate_paper_matrix(self):
        raise NotImplementedError("Calculate paper matrix not implemented")

    def assign_to_topics(self, recompute_all=False):
        raise NotImplementedError("Assign to topics not implemented")

    def related(self, query: str):
        raise NotImplementedError("Related not implemented")

    def _compute_similarity_scores(self, query: str):
        raise NotImplementedError("Compute Similarity Scores not implemented")


class CombinedPaperAnalyzer(PaperAnalyzer):
    class PaperAnalyzerDefinition(PaperAnalyzer):
        """
        This wrapper class handles the paper analyzer objects within this class and gives them additional
        attributes like weight and a name
        """

        def __init__(self, name: str, analyzer: PaperAnalyzer, weight: float, *args, **kwargs):
            super(CombinedPaperAnalyzer.PaperAnalyzerDefinition, self).__init__(*args, **kwargs)
            self.name = name
            self.analyzer = analyzer
            self.weight = weight

            print("Definition", name, analyzer, weight)

        def calculate_paper_matrix(self):
            self.analyzer.calculate_paper_matrix()

        def assign_to_topics(self, recompute_all=False):
            self.analyzer.assign_to_topics(recompute_all)

        def related(self, query: str):
            return self.analyzer.related(query)

        def _compute_similarity_scores(self, query: str):
            return self.analyzer._compute_similarity_scores(query)

    def __init__(self, analyzers: dict, *args, **kwargs):
        """
        :param analyzers: We expect such an analyzer dict:
        {
            "my_paper_analyzer" :   {
                                        "analyzer" : analyzer,
                                        "weight": 0.5
                                    },
            ....
        }
        :param args:
        :param kwargs:
        """
        super(CombinedPaperAnalyzer, self).__init__(*args, **kwargs)

        self.analyzers = list()

        total_weights = 0.0

        for name, obj in analyzers.items():
            self.analyzers.append(CombinedPaperAnalyzer.PaperAnalyzerDefinition(name,
                                                                                obj["analyzer"],
                                                                                obj["weight"]))
            total_weights += obj["weight"]

        assert total_weights == 1.0

    def calculate_paper_matrix(self):
        for analyzer in self.analyzers:
            print("Calculating paper matrix for", analyzer.name)
            analyzer.calculate_paper_matrix()

    def assign_to_topics(self, recompute_all=False):
        for analyzer in self.analyzers:
            print("Assigning topics for", analyzer.name)
            analyzer.assign_to_topics(recompute_all)

    def related(self, query: str):

        paper_ids_lists = list()
        scores_lists = list()

        for analyzer in self.analyzers:
            print("Computing Similarity for", analyzer.name)
            paper_ids, scores = analyzer._compute_similarity_scores(query)

            paper_ids_lists.append(paper_ids)
            scores_lists.append(scores)

        print("All similarities computed")

        papers = Paper.objects.all()

        for paper_ids, scores in paper_ids_lists, scores_lists:
            assert len(paper_ids) == papers.count()

            # We now sort the paper ids so that the scores and ids match.
            paper_ids.sort()
            scores.sort(key=dict(zip(scores, paper_ids)).get)

        paper_ids = paper_ids_lists[0] # All paper ids are the same

        whens = list()

        weights = [analyzer.weight for analyzer in self.analyzers]
        for pk, scores in zip(paper_ids, zip(*scores_lists)):
            score = 100 * sum((score * weight for score, weight in zip(scores, weights)))
            whens.append(models.When(pk=pk, then=score))

        papers = papers.annotate(search_score=models.Case(*whens, output_field=models.FloatField()))

        return papers


class BasicPaperAnalyzer(PaperAnalyzer):

    def __init__(self, type='lda', *args, **kwargs):

        super(BasicPaperAnalyzer, self).__init__(*args, **kwargs)

        self.matrix_file_name = 'paper_matrix.pkl'

        dir_path = os.path.dirname(os.path.realpath(__file__))

        if type == 'lda':
            self.vectorizer = PretrainedLDA(os.path.join(dir_path, 'res/lda.pkl'),
                                            os.path.join(dir_path, 'res/vectorizer.pkl'))
            self.similarity_computer = JensonShannonSimilarity()

            print("Loaded lda vectorizer")
        elif type == 'sentence-transformer':
            from .vectorizer import TitleSentenceVectorizer
            self.vectorizer = TitleSentenceVectorizer()
            self.similarity_computer = CosineDistance()
            self.matrix_file_name = 'paper_matrix_sentence_transformer.pkl'

            print("Loaded paper matrix sentence transformer")
        else:
            raise ValueError('Unknown type')

        self.paper_matrix = None
        matrix_path = os.path.join(dir_path, os.path.join('res', self.matrix_file_name))
        if os.path.exists(matrix_path):
            self.paper_matrix = joblib.load(matrix_path)

    def calculate_paper_matrix(self):

        matrix_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   os.path.join('res', self.matrix_file_name))

        if os.path.exists(matrix_path):
            print(matrix_path, "exists, overwriting..")

        paper = Paper.objects.all()
        matrix = self.vectorizer.vectorize_paper(paper)
        print(matrix.shape)
        id_map = {}
        for index, p in enumerate(paper):
            id_map[p.doi] = index

        self.paper_matrix = {
            'id_map': id_map,
            'index_arr': [p.doi for p in paper],
            'matrix': matrix
        }
        joblib.dump(self.paper_matrix, matrix_path)

        print("Paper matrix exported completely")

    def assign_to_topics(self, recompute_all=False):

        print("Assigning to topics")

        if self.paper_matrix is None:
            raise Exception("Paper matrix empty")

        print("Matrix not empty")

        topics = Topic.objects.all()
        latent_topic_scores = self.vectorizer.vectorize_topics(topics)
        paper = [p for p in Paper.objects.all() if recompute_all or not p.topic_score]
        matrix = self.paper_matrix['matrix']

        print("Begining Paper asignment")

        for p in tqdm(paper):
            arr_index = self.paper_matrix['id_map'][p.doi]
            similarities = self.similarity_computer.similarities(latent_topic_scores, matrix[arr_index])
            most_similar_idx = np.argmax(similarities).item()
            p.topic = topics[most_similar_idx]
            p.topic_score = similarities[most_similar_idx]
            p.save()
        for topic in topics:
            topic.save()

        print("Finished asignment to topics")

    def related(self, query: str):
        paper_ids, scores = self._compute_similarity_scores(query)

        papers = Paper.objects.filter(pk__in=paper_ids)
        whens = list()

        for pk, score in zip(paper_ids, scores):
            whens.append(models.When(pk=pk, then=score * 100))

        papers = papers.annotate(search_score=models.Case(*whens, output_field=models.FloatField()))

        return papers

    def _compute_similarity_scores(self, query: str):
        query_dist = self.vectorizer.vectorize([query])[0]
        matrix = self.paper_matrix['matrix']
        similarity_scores = self.similarity_computer.similarities(matrix, query_dist)
        return self.paper_matrix['index_arr'], similarity_scores
