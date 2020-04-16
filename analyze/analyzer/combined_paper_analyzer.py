from data.models import Paper
from django.db import models

from data.models import Topic
from . import PaperAnalyzer
from collections import defaultdict
import numpy as np

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

        def preprocess(self, force_recompute=False):
            self.analyzer.preprocess(force_recompute)

        def assign_to_topics(self):
            self.analyzer.assign_to_topics()

        def compute_topic_score(self, topics):
            return self.analyzer.compute_topic_score(topics)

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

    def preprocess(self, force_recompute=False):
        for analyzer in self.analyzers:
            print("Calculating paper matrix for", analyzer.name)
            analyzer.preprocess(force_recompute)

    def assign_to_topics(self):
        print("Assigning to topics")

        print("Matrix not empty")
        topics = list(Topic.objects.all())
        print("Beginning Paper assignment")

        all_topic_scores = []

        for analyzer in self.analyzers:
            all_topic_scores.append(analyzer.compute_topic_score(topics))

        papers = Paper.objects.all()

        for paper in papers:

            topic_scores = np.zeros(len(topics))

            for i, analyzer in enumerate(self.analyzers):
                topic_scores += analyzer.weight * np.array(all_topic_scores[i][paper.doi])

            topic_idx = np.argmax(topic_scores).item()
            paper.topic = topics[topic_idx]
            paper.topic_score = topic_scores[topic_idx]
            paper.save()

        for topic in topics:
            topic.save()

        print("Finished asignment to topics")

    def compute_weighted_papers(self, paper_ids_lists, scores_lists):
        papers = Paper.objects.all()

        all_scores = defaultdict(list)
        for paper_ids, scores, analyzer in zip(paper_ids_lists, scores_lists, self.analyzers):
            for doi, score in zip(paper_ids, scores):
                all_scores[doi].append(score * analyzer.weight)

        whens = list()
        for pk, scores in all_scores.items():
            score = 100 * sum(scores)
            whens.append(models.When(pk=pk, then=score))

        papers = papers.annotate(search_score=models.Case(*whens, output_field=models.FloatField()))

        return papers

    def related(self, query: str):
        paper_ids_lists = list()
        scores_lists = list()

        for analyzer in self.analyzers:
            print("Computing Similarity for", analyzer.name)
            paper_ids, scores = analyzer.query(query)

            paper_ids_lists.append(paper_ids)
            scores_lists.append(list(scores))

        print("All similarities computed")

        return self.compute_weighted_papers(paper_ids_lists, scores_lists)

    def get_similar_papers(self, paper_doi: str):
        paper_ids_lists = list()
        scores_lists = list()

        for analyzer in self.analyzers:
            print("Computing Similarity for", analyzer.name)
            paper_ids, scores = analyzer.analyzer.vectorizer.paper_distances(paper_doi)

            paper_ids_lists.append(paper_ids)
            scores_lists.append(list(scores))

        print("All similarities computed")

        return self.compute_weighted_papers(paper_ids_lists, scores_lists)
