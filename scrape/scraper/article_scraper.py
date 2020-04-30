import re

from data.models import Paper, Author


class ArticleScraper(object):
    def __init__(self, log=print):
        self.log = log

    def _get_scrape_method(self):
        raise NotImplementedError

    def _contain_covid19_keywords(self, db_article):
        _COVID19_KEYWORDS = r'(?:covid[ -]?19|sars[ -]?cov[ -]?2)'

        return re.match(_COVID19_KEYWORDS, db_article.title, re.IGNORECASE) \
               or re.match(_COVID19_KEYWORDS, db_article.abstract) \
               or re.match(_COVID19_KEYWORDS, db_article.data.content)

    def _get_or_create_authors(self, authors):
        db_authors = []
        for author in authors:
            db_author, created = Author.objects.get_or_create(
                first_name=author[0],
                last_name=author[1],
            )
            db_author.save()
            db_authors += db_author
        return db_authors

    def _sanitize_content(self, content):
        pass

    def _scrape_content(self, db_article):
        raise NotImplementedError

    def _get_or_create_article(self, doi, title, abstract, authors):
        db_article, _ = Paper.objects.get_or_create(doi=doi)
        db_article.title = title
        db_article.abstract = abstract
        db_article.data_source = self._get_scrape_method()
        db_article.save()
        db_article.authors = self._get_or_create_authors(authors)

        # < get content >

        db_article.covid_related = self._contain_covid19_keywords(db_article)

    def scrape_articles(self, count=None):
        raise NotImplementedError
