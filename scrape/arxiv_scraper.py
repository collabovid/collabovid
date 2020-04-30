import django

django.setup()
# import json

import re
import arxiv

from nameparser import HumanName
from typing import Callable, List, Dict, Tuple, Any
from django.utils.dateparse import parse_datetime

from django.utils import timezone
from data.models import Author, Category, Paper, PaperHost


def _extract_unique_id(article: dict) -> str:
    '''
    Extracts the unique id from an arxiv article.
    :param article: The arXiv article, as dict.
                    'id' is the url, e.g. 'http://arxiv.org/abs/2004.11626v1'
    :return: The unique id, so '2004.11626' in this example.
    '''
    reduced_url = re.sub(r'v(\d+)$', '', article['id'])
    splits = reduced_url.split('/abs/')
    if len(splits) < 2:
        raise Exception
    return splits[1]


def _extract_article_version(article: dict) -> str:
    '''
    Extracts the version number from the arxiv article.
    :param article: The arXiv article, as dict.
    :return: Version number, defaults to 1.
    '''
    version_match = re.match('^\S+v(\d+)$', article['id'])
    if version_match:
        return version_match.group(1)
    else:
        # log_function(f'{db_article.doi}: Could not extract version')
        return None


def _extract_authors(article: dict) -> List[Tuple[str, str]]:
    '''
    Extracts the authors from an arXiv article.
    :param article: The arXiv article, as dict.
    :return:
    '''
    authors = []
    for author in article['authors']:
        human_name = HumanName(author)
        first_name = f'{human_name.first} {human_name.middle}'.strip()
        last_name = human_name.last
        authors.append((first_name, last_name))
    return authors


def _update_detailed_information(db_article: Paper, article: Dict,
                                 log_function: Callable[[Tuple[Any, ...]], Any]) -> bool:
    '''
    Given a article object from the DB, we check the mutable information and refresh them.
    :param db_article: DB article object.
    :param log_function: Used for logging output.
    :return:
    '''
    updated = False

    # TODO: Can we access db_article.version before the article is saved (so for a new article)?
    new_verion = _extract_article_version(article)
    if new_verion != db_article.version:
        updated = True
    db_article.host = PaperHost.objects.get_or_create(name='arXiv')
    db_article.url = article['id']

    authors = _extract_authors(article)
    if len(authors) == 0:
        raise
    db_article.save()

    for author in authors:
        db_author, created = Author.objects.get_or_create(
            first_name=author[0],
            last_name=author[1],
        )
        db_author.save()
        db_article.authors.add(db_author)

    db_article.last_scrape = timezone.now()
    db_article.save()


def _get_or_create_article(
        article: Dict[str, str], update_properties: bool, log_function: Callable[[Tuple[Any, ...]], Any]
) -> Tuple[bool, bool]:
    '''
   Creates or updates a DB article object depending on whether it exists and depending on update_properties
    :param article:
    :param log_function:
    :return: First bool is True, iff article object was created, second one is True, if already existing article object
    was updated.
    '''
    article_id = _extract_unique_id(article)

    try:
        db_article = Paper.objects.get(doi=article_id)
        if update_properties:
            article_version = _extract_article_version(article)
            last_changed = parse_datetime(article['published_at']).date()
            if last_changed > db_article.last_scrape or article_version > db_article.version:
                updated = _update_detailed_information(db_article, log_function)
            else:
                updated = False
            return False, updated
    except Paper.DoesNotExist:
        db_article = Paper(doi=article_id)  # TODO: dont use doi but arxiv id here
        db_article.title = article['title'].replace('\n', ' ')
        db_article.abstract = article['summary'].replace('\n', ' ')
        db_article.internal_source = 'arXiv'
        db_article.published_at = parse_datetime(article['published_at']).date()

        _update_detailed_information(db_article, article, log_function)


def scrape_articles(log_function: Callable[[Tuple[Any, ...]], Any] = print) -> None:
    result = arxiv.query("all:%22COVID 19%22", max_results=1000, iterative=False, sort_by='submittedDate',
                         sort_order='descending')

    for i, article in enumerate(result):
        modify_status = _get_or_create_article(article, False, log_function)


def update_articles(count=200):
    result = arxiv.query("all:%22COVID 19%22", max_results=1000, iterative=False, sort_by='submittedDate',
                         sort_order='ascending')


if __name__ == '__main__':
    scrape_articles()
