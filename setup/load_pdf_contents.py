def run(output):
    from scrape.pdf_content_scraper import PdfContentScraper

    pdf_content_scraper = PdfContentScraper()

    pdf_content_scraper.load_contents()
    output("Assigned lda to topics")


if __name__ == "__main__":
    import django
    django.setup()

    run(print)