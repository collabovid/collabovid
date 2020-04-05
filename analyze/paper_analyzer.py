from analyze.vectorizer import PretrainedLDA
import os

import numpy as np
from data.models import Paper, Topic
from django.db import models
from collections import defaultdict


class PaperAnalyzer:
    def __init__(self, *args, **kwargs):
        pass

    def preprocess(self):
        raise NotImplementedError("Preprocess not implemented")

    def assign_to_topics(self):
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

        def assign_to_topics(self):
            self.analyzer.assign_to_topics()

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

    def preprocess(self):
        for analyzer in self.analyzers:
            print("Calculating paper matrix for", analyzer.name)
            analyzer.preprocess()

    def assign_to_topics(self):
        for analyzer in self.analyzers:
            print("Assigning topics for", analyzer.name)
            analyzer.assign_to_topics()

    def related(self, query: str):

        paper_ids_lists = list()
        scores_lists = list()

        for analyzer in self.analyzers:
            print("Computing Similarity for", analyzer.name)
            paper_ids, scores = analyzer.query(query)

            paper_ids_lists.append(paper_ids)
            scores_lists.append(list(scores))

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

    TYPE_LDA = 'lda'
    TYPE_SENTENCE_TRANSFORMER = 'sentence-transformer'

    def __init__(self, type=TYPE_LDA, *args, **kwargs):

        super(BasicPaperAnalyzer, self).__init__(*args, **kwargs)
        dir_path = os.path.dirname(os.path.realpath(__file__))

        self.type = type

        if type == BasicPaperAnalyzer.TYPE_LDA:
            self.vectorizer = PretrainedLDA(os.path.join(dir_path, 'res/lda.pkl'),
                                            os.path.join(dir_path, 'res/vectorizer.pkl'),
                                            matrix_file_name="paper_matrix.pkl")
            print("Loaded lda vectorizer")
        elif type == BasicPaperAnalyzer.TYPE_SENTENCE_TRANSFORMER:
            from .vectorizer import SentenceVectorizer
            self.vectorizer = SentenceVectorizer(matrix_file_name="paper_matrix_sentence_transformer.pkl")
            print("Loaded paper matrix sentence transformer")
        else:
            raise ValueError('Unknown type')

    def preprocess(self):
        self.vectorizer.generate_paper_matrix()

    def query(self, query: str):
        embedding = self.vectorizer.vectorize([query])[0]
        return self.vectorizer.compute_similarity_scores(embedding)

    def assign_to_topics(self):

        print("Assigning to topics")

        if self.vectorizer.paper_matrix is None:
            raise Exception("Paper matrix empty")

        print("Matrix not empty")
        topics = list(Topic.objects.all())
        print("Begining Paper asignment")

        if self.type == BasicPaperAnalyzer.TYPE_SENTENCE_TRANSFORMER:
            topic_scores = self._topics_scores_sentence_transofrmer(topics)
        else:
            topic_scores = defaultdict(list)
            topic_title_embeddings, topic_description_embeddings = self.vectorizer.vectorize_topics(topics)

            for idx, topic in enumerate(topics):
                paper_ids, similarities = self.vectorizer.compute_similarity_scores(topic_title_embeddings[idx])

                for id, score in zip(paper_ids, similarities):
                    topic_scores[id].append(score)

        papers = Paper.objects.all()
        for paper in papers:
            topic_idx = np.argmax(topic_scores[paper.doi]).item()
            paper.topic = topics[topic_idx]
            paper.topic_score = topic_scores[paper.doi][topic_idx]
            paper.save()

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

    def _topics_scores_sentence_transofrmer(self, topics):
        topic_scores = defaultdict(list)
        topic_title_embeddings, topic_description_embeddings = self.vectorizer.vectorize_topics(topics)

        for idx, topic in enumerate(topics):

            paper_ids, title_similarities = self.vectorizer.compute_similarity_scores(topic_title_embeddings[idx])

            similarities = 1.0 * title_similarities

            if False:
                description_similarities_raw = list()

                for vec in topic_description_embeddings[idx]:
                    _, similarities = self.vectorizer.compute_similarity_scores(vec)
                    description_similarities_raw.append(similarities)

                description_similarities = np.array([sum(similarities_for_paper) / len(similarities_for_paper)
                                                     for similarities_for_paper in zip(*description_similarities_raw)])
                title_similarities = np.array(title_similarities)

                similarities = 1.0 * title_similarities + 0.0 * description_similarities

            for id, score in zip(paper_ids, similarities):
                topic_scores[id].append(score)

        return topic_scores
