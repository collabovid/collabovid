from django.db import models
from django.conf import settings
import os
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

class Task(models.Model):
    STATUS_PENDING = 0
    STATUS_FINISHED = 1
    STATUS_ERROR = -1
    STATUS_ABORTED = -2

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_FINISHED, "Finished"),
        (STATUS_ERROR, "Error"),
        (STATUS_ABORTED, "Aborted")
    )

    name = models.CharField(max_length=200)

    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING)
    started_by = models.CharField(max_length=200)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def log_file(self):
        return os.path.join(settings.TASK_LOGGING_PATH, str(self.pk) + ".log")


@receiver(post_delete, sender=Task)
def _task_delete(sender, instance, **kwargs):
    if os.path.exists(instance.log_file):
        os.remove(instance.log_file)