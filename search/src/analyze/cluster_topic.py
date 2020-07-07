from tasks.definitions import Runnable, register_task
from . import get_vectorizer
from data.models import Paper, Topic
from sklearn.cluster import KMeans, AgglomerativeClustering
import numpy as np
from .utils import get_top_n_words, get_predictive_words
import joblib


@register_task
class ClusterTopic(Runnable):

    @staticmethod
    def task_name():
        return "cluster-topic"

    def __init__(self, topic_id: int, vectorizer_name: str = 'transformer-paper-oubiobert-512', n_clusters: int = 2,
                 *args,
                 **kwargs):
        super(ClusterTopic, self).__init__(*args, **kwargs)
        self.topic_id = topic_id
        self._vectorizer_name = vectorizer_name
        self.n_clusters = n_clusters

    def run(self):
        self.log("Starting ClusterTopic of topic: ", self.topic_id)
        vectorizer = get_vectorizer(self._vectorizer_name)
        paper_matrix = vectorizer.paper_matrix
        X = 0.5 * paper_matrix['abstract'] + 0.5 * paper_matrix['title']
        id_map = paper_matrix['id_map']

        old_topic = Topic.objects.get(pk=self.topic_id)
        papers = list(old_topic.papers.all())
        paper_dois = [paper.doi for paper in papers]
        matrix_indices = [id_map[doi] for doi in paper_dois]
        sub_matrix = X[matrix_indices]
        clustering = KMeans(n_clusters=self.n_clusters).fit(sub_matrix)
        self.log("Finished computing clustering")
        clusters = clustering.labels_

        topics = []
        titles_list = []
        for cluster in self.progress(range(len(np.unique(clusters)))):
            topic = Topic()
            topic.save()
            titles = []
            for i, paper in enumerate(papers):
                if clusters[i] == cluster:
                    titles.append(paper.title)
                    paper.topic = topic
                    paper.save()
            topics.append(topic)
            self.log(f'Added new Topic with {len(titles)} papers')
            titles_list.append(titles)

        top_words = get_predictive_words(titles_list, top=50)
        for topic, words in zip(topics, top_words):
            topic.name = 'Generated: ' + ', '.join(words[:7])
            topic.description = ', '.join(words)
            topic.description_html = ', '.join(words)
            topic.icon_path = '#'
            topic.save()
            self.log(f'Assigned Title to topic: {topic.name}')

        self.log('Deleting old topic: ', old_topic.name)
        old_topic.delete()
        self.log('ClusterTopic Finished')
