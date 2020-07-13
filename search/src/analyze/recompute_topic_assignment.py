from tasks.definitions import Runnable, register_task
from . import get_vectorizer
from data.models import Paper, Topic
from sklearn.cluster import KMeans
import numpy as np
from .utils import get_predictive_words
import joblib
from collections import defaultdict


@register_task
class RecomputeTopicAssignment(Runnable):

    @staticmethod
    def task_name():
        return "recompute-topic-assignment"

    @staticmethod
    def description():
        return "Computes a full clustering of the paper embeddings and assigns all papers to newly created topics."

    def __init__(self, n_clusters: int = 48, vectorizer_name: str = 'transformer-paper-nearest-512', *args, **kwargs):
        super(RecomputeTopicAssignment, self).__init__(*args, **kwargs)
        self._vectorizer_name = vectorizer_name
        self.n_clusters = n_clusters

    def run(self):
        self.log("Starting RecomputeTopicAssignment")
        vectorizer = get_vectorizer(self._vectorizer_name)
        paper_matrix = vectorizer.paper_matrix
        X = 0.5 * paper_matrix['abstract'] + 0.5 * paper_matrix['title']
        clustering = KMeans(n_clusters=self.n_clusters).fit(X)
        clusters = clustering.labels_
        id_map = paper_matrix['id_map']

        # delete all old topics
        old_topics = list(Topic.objects.all())

        papers = Paper.objects.all()
        # clusters = np.random.randint(low=0, high=20, size=len(papers))
        topics = []

        titles_list = []

        for cluster in self.progress(range(len(np.unique(clusters)))):
            topic = Topic()
            topic.save()
            titles = []
            topic_occurrences_dict = defaultdict(int)
            for paper in papers:
                matrix_index = id_map[paper.doi]
                if clusters[matrix_index] == cluster:
                    titles.append(paper.title)
                    if paper.topic:
                        topic_occurrences_dict[paper.topic.name] += 1
                    paper.topic = topic
                    paper.save()
            if len(topic_occurrences_dict) > 0:
                best_matching_old_topic = max(list(topic_occurrences_dict.items()), key=lambda x: x[1])
                topic.name = best_matching_old_topic[0]
                topic.overlapping_paper_count = best_matching_old_topic[1]

            topics.append(topic)
            titles_list.append(titles)

        top_words = get_predictive_words(titles_list, top=50)
        for topic, words in zip(topics, top_words):
            if not topic.name:
                topic.name = ', '.join(words[:7])
            topic.keywords = ', '.join(words)
            topic.save()

        for topic in old_topics:
            topic.delete()

        print('RecomputeTopicAssignment Finished')
