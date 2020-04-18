if __name__ == "__main__":
    import django
    django.setup()

    from scrape.pdf_content_scraper import PdfContentScraper
    from tasks.task_runner import TaskRunner

    TaskRunner.run_task(PdfContentScraper, scrape_images=False, started_by="Setup Script")
