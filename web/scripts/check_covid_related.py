if __name__ == '__main__':
    import django
    django.setup()

    from scrape.task_check_covid_related import CheckCovidRelatedTask
    from tasks.task_runner import TaskRunner

    TaskRunner.run_task(CheckCovidRelatedTask, started_by="Setup Script")