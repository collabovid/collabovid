"""
Runs a given task or returns a list of available tasks for this service.
"""
import os
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

    from tasks.task_runner import CommandLineTaskRunner
    CommandLineTaskRunner.run_task()


