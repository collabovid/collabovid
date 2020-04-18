from tasks import Runnable, register_task
from . import get_topic_assignment_analyzer


@register_task
class UpdateTopicAssignment(Runnable):

    @staticmethod
    def task_name():
        return "update-topic-assignment"

    def __init__(self, *args, **kwargs):
        super(UpdateTopicAssignment, self).__init__(*args, **kwargs)

    def run(self):
        self.log("Updating topic assignment")
        self.log("Assigning papers to topics...")
        get_topic_assignment_analyzer().assign_to_topics()
        self.log("Finished updating paper matrices and topic assignment")
