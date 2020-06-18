from django.db import models

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

    log = models.TextField(default="")

    progress = models.IntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(auto_now=True)