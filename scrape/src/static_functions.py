import re
from datetime import date


def covid_related(db_article):
    if db_article.published_at and db_article.published_at < date(year=2019, month=12, day=1):
        return False

    COVID19_KEYWORDS = r'(corona.?virus|(^|\s)corona(\s|$)|covid.?19|(^|\s)covid(\s|$)|sars.?cov.?2|2019.?ncov)'

    return bool(re.search(COVID19_KEYWORDS, db_article.title, re.IGNORECASE)) \
           or bool(re.search(COVID19_KEYWORDS, db_article.abstract, re.IGNORECASE)) \
           or bool((db_article.data and re.search(COVID19_KEYWORDS, db_article.data.content, re.IGNORECASE)))