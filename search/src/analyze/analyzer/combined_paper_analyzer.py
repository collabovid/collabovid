from data.models import Paper
from django.db import models

from data.models import Topic
from . import PaperAnalyzer
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