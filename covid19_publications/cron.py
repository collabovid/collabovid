from scrape.scrape_articles import Scrape
from datetime import datetime


def update_paper():
    now = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
    print(now)
    Scrape()
