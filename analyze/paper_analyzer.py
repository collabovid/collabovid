from .vectorizer import PretrainedLDA, TextVectorizer
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

    def preprocess(self):
        raise NotImplementedError("Calculate paper matrix not implemented")

    def assign_to_topics(self, recompute_all=False):
        raise NotImplementedError("Assign to topics not implemented")

    def related(self, query: str):
        raise NotImplementedError("Related not implemented")

    def query(self, query: str):
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

        def preprocess(self):
            self.analyzer.preprocess()

        def assign_to_topics(self, recompute_all=False):
            self.analyzer.assign_to_topics(recompute_all)

        def related(self, query: str):
            return self.analyzer.related(query)

        def query(self, query: str):
            return self.analyzer.query(query)

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
            analyzer.preprocess()

    def assign_to_topics(self, recompute_all=False):
        for analyzer in self.analyzers:
            print("Assigning topics for", analyzer.name)
            analyzer.assign_to_topics(recompute_all)

    def related(self, query: str):

        paper_ids_lists = list()
        scores_lists = list()

        for analyzer in self.analyzers:
            print("Computing Similarity for", analyzer.name)
            paper_ids, scores = analyzer.query(query)

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
        dir_path = os.path.dirname(os.path.realpath(__file__))

        if type == 'lda':
            self.vectorizer = PretrainedLDA(os.path.join(dir_path, 'res/lda.pkl'),
                                            os.path.join(dir_path, 'res/vectorizer.pkl'),
                                            matrix_file_name="paper_matrix.pkl")
            print("Loaded lda vectorizer")
        elif type == 'sentence-transformer':
            from .vectorizer import SentenceVectorizer
            self.vectorizer = SentenceVectorizer(matrix_file_name="paper_matrix_sentence_transformer.pkl")
            print("Loaded paper matrix sentence transformer")
        else:
            raise ValueError('Unknown type')

    def preprocess(self):
        self.vectorizer.generate_paper_matrix()

    def query(self, query: str):
        return self.vectorizer.compute_similarity_scores(query)

    def assign_to_topics(self, recompute_all=False):

        print("Assigning to topics")

        if self.vectorizer.paper_matrix is None:
            raise Exception("Paper matrix empty")

        print("Matrix not empty")

        topics = Topic.objects.all()
        paper = [p for p in Paper.objects.all() if recompute_all or not p.topic_score]

        print("Begining Paper asignment")

        paper_ids, similarities = self.vectorizer.compute_similarity_scores(topics, TextVectorizer.VECTORIZE_TOPIC)

        for p in tqdm(paper):

            current_similarities = similarities[paper_ids.index(p.doi)]
            most_similar_idx = np.argmax(current_similarities).item()
            p.topic = topics[most_similar_idx]
            p.topic_score = current_similarities[most_similar_idx]
            p.save()
        for topic in topics:
            topic.save()

        print("Finished asignment to topics")

    def related(self, query: str):
        paper_ids, scores = self.query(query)

        papers = Paper.objects.filter(pk__in=paper_ids)
        whens = list()

        for pk, score in zip(paper_ids, scores):
            whens.append(models.When(pk=pk, then=score * 100))

        papers = papers.annotate(search_score=models.Case(*whens, output_field=models.FloatField()))

        return papers

