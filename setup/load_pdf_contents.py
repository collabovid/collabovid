if __name__ == "__main__":
    import django
    django.setup()

    from scrape.pdf_content_scraper import PdfContentScraper
    from scrape.scrape import Scrape
    from tasks.task_runner import TaskRunner

    TaskRunner.run_task_async(cls=Scrape, scrape_images=False)
