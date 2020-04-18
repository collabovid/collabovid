if __name__ == "__main__":
    import django
    django.setup()

    from tasks.models import Task
    for task in Task.objects.filter(status=Task.STATUS_PENDING):
        task.status = Task.STATUS_ABORTED
        task.save()
