from scrape.scrape import Scrape
from scrape.task_arxiv_update import ArxivUpdateTask
from scrape.task_medrxiv_update import MedBiorxivUpdateTask
from datetime import datetime
from tasks.task_runner import TaskRunner
from analyze.setup_vectorizer import SetupVectorizer
from analyze.update_topic_assignment import UpdateTopicAssignment


def print_time(name):
    now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
    print(now, name)


def scrape_new_paper():
    print_time("Scrape New Paper")
    TaskRunner.run_task(Scrape, started_by="Cron")


def update_paper():
    print_time("Update Paper")
    TaskRunner.run_task(ArxivUpdateTask, started_by="Cron")
    TaskRunner.run_task(MedBiorxivUpdateTask, started_by="Cron")

    TaskRunner.run_task(SetupVectorizer, force_recompute=True, started_by="Cron")
    TaskRunner.run_task(UpdateTopicAssignment, started_by="Cron")
