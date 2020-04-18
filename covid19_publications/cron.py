from scrape.scrape import Scrape
from datetime import datetime
from tasks.task_runner import TaskRunner


def update_paper():
    now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
    print(now)
    TaskRunner.run_task(Scrape, started_by="Cron")
