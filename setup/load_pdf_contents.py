if __name__ == "__main__":
    import django
    django.setup()

    from scrape.pdf_content_scraper import PdfContentScraper
    from tasks.task_runner import TaskRunner
    from data.models import Paper

    print(PdfContentScraper)
    TaskRunner.run_task_async(cls=PdfContentScraper, papers=Paper.objects.all())
