import json
import re
from typing import Callable, List, Dict, Tuple, Any

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from data.models import PaperHost, Paper, Author, Category

_COVID_JSON_URL = 'https://connect.medrxiv.org/relate/collection_json.php?grp=181'
_MEDRXIV_URL = 'https://www.medrxiv.org/content/{0}'
_BIORXIV_URL = 'https://www.biorxiv.org/content/{0}'


def _get_article_json() -> List[Dict[str, str]]:
    """
    Downloads the list of all COVID-19 related articles from medRxiv in JSON format (which also includes articles on
    bioRxiv).

    :return: Dict of information, provided in JSON.
    """
    try:
        response = requests.get(_COVID_JSON_URL)
        return json.loads(response.text)['rels']
    except requests.exceptions.ConnectionError as ex:
        raise Exception("Unable to download medRxiv COVID-19 article list JSON")


def _get_or_create_paperhost(paperhost_name: str) -> PaperHost:
    """
    Gets or creates a paper host DB object from its name and saves to DB.

    :param paperhost_name: Name of the paper host. Should be either 'medrxiv' or 'biorxiv'.
    :return: Created or gotten paper host DB object.
    """
    if paperhost_name == "medrxiv":
        paperhost_name = "medRxiv"
        url = 'https://www.medrxiv.org'
    elif paperhost_name == "biorxiv":
        paperhost_name = "bioRxiv"
        url = 'https://www.biorxiv.org'
    else:
        url = None

    host, created = PaperHost.objects.get_or_create(
        name=paperhost_name,
        url=url,
    )
    if created:
        host.save()

    return host


def _extract_authors_information(soup: BeautifulSoup) -> List[Tuple[str, str, bool]]:
    """
    Extracts authors information from HTML soup.

    :param soup: HTML soup of detailed article page.
    :return: List of tuples of first name, last name and bool, if author is first author of article.
    """
    author_webelements = soup.find(
        'span', attrs={'class': 'highwire-citation-authors'}
    ).find_all('span', recursive=False)

    authors = []
    for author_webelement in author_webelements:
        try:
            firstname = author_webelement.find('span', attrs={'class': 'nlm-given-names'}).text
            name = author_webelement.find('span', attrs={'class': 'nlm-surname'}).text
            first_author = 'first' in author_webelement['class']
            authors.append((firstname, name, first_author))
        except AttributeError:
            # Ignore collaboration groups, listed in authors list
            continue

    return authors


def _extract_category(soup: BeautifulSoup) -> str:
    """
    Extracts article category from HTML soup.

    :param soup: HTML soup of detailed article page.
    :return: Category name, provided on detailed page. "Unknown", if not provided.
    """
    categories = soup.find_all('span', {'class': 'highwire-article-collection-term'})
    if len(categories) == 0:
        return "Unknown"
    else:
        return categories[0].text.strip()


class _PdfUrlNotFoundException(Exception):
    pass


def _extract_relative_pdf_url(soup: BeautifulSoup) -> str:
    """
    Extracts PRF URL from HTML soup. Throws Exception, if URL cannot be extracted.

    :param soup: HTML soup of detailed article page.
    :return: URL to article PDF.
    """
    dl_element = soup.find('a', attrs={'class': 'article-dl-pdf-link link-icon'})

    if dl_element and dl_element.has_attr('href'):
        relative_url = dl_element['href']
        return relative_url
    else:
        raise _PdfUrlNotFoundException


def _update_detailed_information(db_article: Paper, log_function: Callable[[Tuple[Any, ...]], Any]) -> bool:
    """
    Given a DB article object and an article URL, detailed information from the articles detail page are extracted.
    The log function is used for log output.

    :param db_article: DB article object.
    :param log_function: Function, called for logging output.
    :return: True, if article was updated.
    """
    updated = False

    response = requests.get(db_article.url)
    redirected_url = response.url

    version_match = re.match('^\S+v(\d+)$', redirected_url)
    if version_match:
        article_version = version_match.group(1)
    else:
        log_function(f'{db_article.doi}: Could not extract version')
        article_version = None

    if db_article.version != article_version:
        db_article.version = article_version
        updated = True

    soup = BeautifulSoup(response.text, 'html.parser')
    if not db_article.pdf_url:
        db_article.pdf_url = db_article.host.url + _extract_relative_pdf_url(soup)
        updated = True

    category = _extract_category(soup)

    db_category_name = None

    try:
        db_category_name = db_article.category.name
    except Category.DoesNotExist:
        pass

    if not db_category_name or category != db_category_name:
        db_category, created = Category.objects.get_or_create(
            name=category,
        )
        db_category.save()
        db_article.category = db_category
        updated = True

    db_article.save()  # Has to be saved before adding authors

    authors = _extract_authors_information(soup)
    if len(authors) != 0:
        db_article.authors.clear()
        for author in authors:
            db_author, created = Author.objects.get_or_create(
                first_name=author[0],
                last_name=author[1],
            )
            db_author.save()
            db_article.authors.add(db_author)
        updated = True
    db_article.last_scrape = timezone.now()
    db_article.save()

    return updated


def _get_or_create_article(
        article: Dict[str, str], update_unknown_category: bool, log_function: Callable[[Tuple[Any, ...]], Any]
) -> Tuple[bool, bool]:
    """
    Gets or create a DB article object.

    :param article: Article information, extracted from medRxiv JSON.
    :param update_unknown_category: If true, the detailed information of all articles with category 'Unkown' are
    updated.
    :param log_function: Function, called for logging output.
    :return: First bool is True, iff article object was created, second one is True, if already existing article object
    was updated.
    """
    try:
        db_article = Paper.objects.get(doi=article['rel_doi'])

        if db_article.category_id == 'Unknown' and update_unknown_category:
            updated = _update_detailed_information(db_article, log_function)
        else:
            updated = False

        return False, updated
    except Paper.DoesNotExist:
        db_article = Paper(doi=article['rel_doi'])

        db_article.title = article['rel_title']
        db_article.url = article['rel_link']
        db_article.abstract = article['rel_abs']
        db_article.published_at = article['rel_date']
        db_article.host = _get_or_create_paperhost(article['rel_site'])

        _update_detailed_information(db_article, log_function)

        return True, False


def scrape_articles(update_unknown_category: bool = True, log_function: Callable[[Tuple[Any, ...]], Any] = print) -> None:
    """
    Scrapes all new articles from medRxiv/bioRxiv.

    :param update_unknown_category: If true, the detailed information of all articles with category 'Unkown' are
    updated.
    :param log_function: Function, called for logging output.
    """
    article_json = _get_article_json()

    count_created = 0
    count_updated = 0
    errors = 0

    for article in article_json:
        doi = article['rel_doi']
        try:
            modify_status = _get_or_create_article(article, update_unknown_category, log_function)
        except _PdfUrlNotFoundException:
            # Article is not created, if the PDF URL is not available.
            log_function(f"Could not find PDF URL for {doi}, skip article")
            errors += 1
            continue

        if modify_status[0]:
            log_function(f"Created DB record for {doi}")
            count_created += 1
        elif modify_status[1]:
            log_function(f"Updated DB record for {doi}")
            count_updated += 1
        else:
            log_function(f"Skipped article {doi}")

    log_function(f"Created/Updated: {count_created}/{count_updated}")
    if errors > 0:
        log_function(f"Finished with {errors} errors")
        raise Exception()


def update_articles(count: int = None, log_function: Callable[[Tuple[Any, ...]], Any] = print):
    """
    Update detailed article information in DB.

    :param count: Number of article updates, begin with earliest updated ones.
    :param log_function: Function, called for logging output.
    """
    updated = 0

    articles = Paper.objects.all().order_by('last_scrape')
    if count:
        articles = articles[:count]

    for article in articles:
        if _update_detailed_information(article, log_function):
            updated += 1
            log_function(f"Updated article {article.doi}")

    log_function(f"Updated {updated} articles")


def delete_revoked_articles(log_function: Callable[[Tuple[Any, ...]], Any] = print) -> List[str]:
    """
    Remove all revoked articles (no longer in JSON file) from DB.

    :return: List of dois of removed articles.
    """
    json_dois = [article['rel_doi'] for article in _get_article_json()]

    revoked_articles = []
    for db_article in Paper.objects.all():
        if db_article.doi not in json_dois:
            revoked_articles.append(db_article.doi)
            log_function(f"Deleting article {db_article.doi}")

    Paper.objects.filter(doi__in=revoked_articles).delete()

    log_function(f"Deleted {len(revoked_articles)} articles")
    return revoked_articles
