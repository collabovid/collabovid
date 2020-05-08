import os
import argparse
import django

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrape.settings_dev')
    django.setup()

    from src.scrape import *
    from src.pdf_content_scraper import *
    from src.medrxiv_scraping_task import *
    from src.citation_refresher import *
    from src.pdf_image_scraper import *
    from src.pdf_scraper import *
    from tasks.definitions import AVAILABLE_TASKS
    from tasks.task_runner import TaskRunner

    parser = argparse.ArgumentParser()
    parser.add_argument('task')
    parser.add_argument('-u', '--user', default='default')
    args = parser.parse_args()
    task_name = args.task

    if task_name not in AVAILABLE_TASKS:
        print('Error Unknown Task: ', args.task)
        exit(1)
    task_cls = AVAILABLE_TASKS[task_name]
    TaskRunner.run_task(task_cls, started_by=args.user)

