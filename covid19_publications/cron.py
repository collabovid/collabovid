from scrape.scrape_articles import scrape_articles
from datetime import datetime


def update_paper():
    now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
    print(now)
    scrape_articles()
