import re
import arxiv

from nameparser import HumanName
from typing import Callable, List, Dict, Tuple, Any, Optional
from django.utils.dateparse import parse_datetime

from django.utils import timezone
from data.models import Author, Paper, PaperHost, DataSource


_ARXIV_WITHDRAWN_NOTICE = 'This paper has been withdrawn by the author(s)'


class _AuthorsNotExtractableException(Exception):
    pass


def _extract_unique_id(article: Dict) -> str:
    """
    Extracts the unique id from an arxiv article.
    :param article: The arXiv article, as dict.
                    'id' is the url, e.g. 'http://arxiv.org/abs/2004.11626v1'
    :return: The unique id, so '2004.11626' in this example.
    """
    reduced_url = re.sub(r'v(\d+)$', '', article['id'])
    splits = reduced_url.split('/abs/')
    if len(splits) < 2:
        raise Exception
    return splits[1]


def _extract_article_version(article: Dict) -> Optional[int]:
    """
    Extracts the version number from the arxiv article.
    :param article: The arXiv article, as dict.
    :return: Version number, defaults to 1.
    """
    version_match = re.match('^\S+v(\d+)$', article['id'])
    if version_match:
        return int(version_match.group(1))
    else:
        return None


def _extract_authors(article: Dict) -> List[Tuple[str, str]]:
    """
    Extracts the authors from an arXiv article.
    :param article: The arXiv article, as dict.
    :return: List of authors in format (firstname, listname).
    """
    authors = []
    for author in article['authors']:
        human_name = HumanName(author)
        first_name = f'{human_name.first} {human_name.middle}'.strip()
        last_name = human_name.last
        authors.append((first_name, last_name))
    return authors


def _update_detailed_information(db_article: Paper, article: Dict,
                                 log_function: Callable[[Any], Any]) -> bool:
    """
    Given a article object from the DB, we check the mutable information and refresh them.
    :param db_article: DB article object.
    :param log_function: Used for logging output.
    :return: True iff the updating finished successfully.
    """
    if _ARXIV_WITHDRAWN_NOTICE in article['title']:
        log_function(f'Article {article["id"]} was withdrawn. We mark it as withdrawn.')
        # db_article.withdrawn = True
        # db_article.save()
        # TODO: Mark as withdrawn after Yannic's migrations.

    new_version = _extract_article_version(article)
    if not new_version:
        log_function(f'{db_article.doi}: Could not extract version.')
    elif new_version != db_article.version:
        db_article.version = new_version

    db_article.host, _ = PaperHost.objects.get_or_create(name='arXiv',
                                                         url='https://www.arxiv.org')
    db_article.url = article['id']
    db_article.pdf_url = article['pdf_url']
    arxiv_data_source, _ = DataSource.objects.get_or_create(name='arxiv-scraper')
    db_article.data_source = arxiv_data_source
    authors = _extract_authors(article)
    if len(authors) == 0:
        raise _AuthorsNotExtractableException
    else:
        db_article.save()

    db_article.authors.clear()
    for author in authors:
        db_author, created = Author.objects.get_or_create(
            first_name=author[0],
            last_name=author[1],
            data_source=arxiv_data_source,
            split_name=True
        )
        db_author.save()
        db_article.authors.add(db_author)

    db_article.last_scrape = timezone.now()
    db_article.save()
    return True


def _get_or_create_article(
        article: Dict[str, str], log_function: Callable[[Any], Any]
) -> Tuple[bool, bool]:
    """
    Creates or updates a DB article object depending on whether it exists.
    :param article: The Dict of the article (dict from arXiv API)
    :param log_function:
    :return: First bool is True, iff article object was created, second one is True, if already existing article object
    was updated.
    """
    article_id = _extract_unique_id(article)
    updated = False

    try:
        db_article = Paper.objects.get(doi=article_id)
        article_version = _extract_article_version(article)
        last_changed = parse_datetime(article['updated'])
        if not db_article.last_scrape or \
                last_changed > db_article.last_scrape or \
                article_version > db_article.version:
            updated = _update_detailed_information(db_article, article, log_function)
        else:
            updated = False
        return False, updated

    except Paper.DoesNotExist:
        if _ARXIV_WITHDRAWN_NOTICE in article['title']:
            log_function(f'Article {article["id"]} was withdrawn. We do not add it.')
            return False, False

        db_article = Paper(doi=article_id)  # TODO: Save to extra arXiv ID field?
        db_article.title = article['title'].replace('\n', ' ')
        db_article.abstract = article['summary'].replace('\n', ' ')
        db_article.published_at = parse_datetime(article['published']).date()

        _update_detailed_information(db_article, article, log_function)
        return True, False


def scrape_articles(max_new_created: int = None, log_function: Callable[[Any], Any] = print):
    """
    Scrape new articles.
    :param max_new_created: Maximum number of new articles to create. We stop after this amount.
    :param log_function: Function used for logging.
    """
    created, updated, errors = 0, 0, 0
    article_created, article_updated = False, False
    query_result = arxiv.query("all:%22COVID 19%22", max_results=1000, iterative=False, sort_by='submittedDate',
                               sort_order='descending')
    # TODO: Split the query into smaller chunks?
    for i, article in enumerate(query_result):
        if max_new_created and created >= max_new_created:
            log_function(f'Stopping after given number of {max_new_created} created articles.')
            break
        try:
            article_created, article_updated = _get_or_create_article(article, log_function)
        except _AuthorsNotExtractableException:
            log_function(f"Authors not extractable for {article['id']}. Did not save to DB.")
            errors += 1
        except KeyError as e:
            log_function(f"Skipping {article['id']} due to a Key Error. {str(e)}")
            errors += 1

        if article_created:
            log_function(f"Created DB record for {article['id']}")
            created += 1
        elif article_updated:
            log_function(f"Updated DB record for {article['id']}")
            updated += 1
        else:
            log_function(f"Skipped article {article['id']}")

    log_function(f"Created/Updated: {created}/{updated}")

    if errors > 0:
        log_function(f"Finished with {errors} errors")
        raise Exception()
