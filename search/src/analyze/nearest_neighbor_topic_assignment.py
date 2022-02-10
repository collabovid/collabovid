from tasks.definitions import Runnable, register_task
from . import get_similar_paper_finder
from data.models import Paper, Topic
from collections import defaultdict


@register_task
class NearestNeighborTopicAssignment(Runnable):

    @staticmethod
    def task_name():
        return "nearest-neighbor-topic-assignment"

    @staticmethod
    def description():
        return "Assigns all unassigned papers to a topic through a majority vote of the nearest neighbors."

    def __init__(self, n_neighbors: int = 15, *args, **kwargs):
        super(NearestNeighborTopicAssignment, self).__init__(*args, **kwargs)
        self._n_neighbors = n_neighbors

    def run(self):
        self.log("Starting NearestNeighborTopicAssignment")
        similar_paper_finder = get_similar_paper_finder()

        papers = Paper.objects.all()
        paper_topic_dict = {}
        for paper in papers:
            if paper.topic:
                paper_topic_dict[paper.doi] = paper.topic.pk

        for paper in self.progress(papers):
            if not paper.topic:
                similar_papers = similar_paper_finder.similar(doi=paper.doi, top=self._n_neighbors)
                topic_occurrences = defaultdict(float)
                for doi, score in similar_papers:
                    if doi in paper_topic_dict:
                        topic_id = paper_topic_dict[doi]
                        topic_occurrences[topic_id] += score

                if len(topic_occurrences) > 0:
                    topic_id, occurrences = max(list(topic_occurrences.items()), key=lambda x: x[1])
                    paper.topic = Topic.objects.get(pk=topic_id)
                    paper.save()
                    self.log(f"Assigned {paper.title} to topic: {paper.topic.name}")
                else:
                    self.log(f"Skipped {paper.title} because there were no topics.")

        print('NearestNeighborTopicAssignment Finished')
