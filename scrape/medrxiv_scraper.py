import json
import re
from datetime import timedelta
from timeit import default_timer as timer
from typing import Callable, List, Dict, Tuple, Any

import requests
from bs4 import BeautifulSoup
from django.db import IntegrityError
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
    except requests.exceptions.ConnectionError:
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


class _ScrapeException(Exception):
    def __init__(self, msg):
        self.msg = msg


def _get_or_create_author(first_name, last_name, orcid):
    try:
        db_author, created = Author.objects.get_or_create(
            first_name=first_name,
            last_name=last_name,
            orcid=orcid,
        )
        return db_author
    except IntegrityError:
        # Other author with same ORCID already in db.
        # Check if one author has second name.
        duplicate = Author.objects.filter(orcid=orcid)[0]
        if duplicate.orcid == orcid and duplicate.last_name.lower() == last_name.lower() \
                and duplicate.first_name.split()[0].lower() == first_name.split()[0].lower():
            if len(first_name) > len(duplicate.first_name):
                duplicate.first_name = first_name
                duplicate.save()
            return duplicate
        raise _ScrapeException(f"Author {first_name} {last_name}, ORCID {orcid} not unique")


def _extract_authors_information(soup: BeautifulSoup):
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
            first_name = author_webelement.find('span', attrs={'class': 'nlm-given-names'}).text
            last_name = author_webelement.find('span', attrs={'class': 'nlm-surname'}).text
            # first_author = 'first' in author_webelement['class']

            orcid = None
            if author_webelement.find('a'):
                orcid_match = re.fullmatch(
                    r'http://orcid.org/(\d{4}-\d{4}-\d{4}-\d{3}[\dXx])',
                    author_webelement.find('a')['href'],
                )
                if orcid_match:
                    orcid = orcid_match.group(1)

            authors.append(_get_or_create_author(first_name, last_name, orcid))
        except AttributeError:
            # Ignore collaboration groups, listed in authors list
            continue

    if len(authors) == 0:
        raise _ScrapeException("Could not found author elements in soup")
    return authors


def _extract_category(soup: BeautifulSoup) -> str:
    """
    Extracts article category from HTML soup.

    :param soup: HTML soup of detailed article page.
    :return: Category name, provided on detailed page. "Unknown", if not provided.
    """
    categories = soup.find_all('span', {'class': 'highwire-article-collection-term'})
    if len(categories) == 0:
        category = "Unknown"
    else:
        category = categories[0].text.strip()

    db_category, created = Category.objects.get_or_create(name=category)
    db_category.save()
    return db_category


def _extract_relative_pdf_url(soup: BeautifulSoup) -> str:
    """
    Extracts PRF URL from HTML soup. Throws Exception, if URL cannot be extracted.

    :param soup: HTML soup of detailed article page.
    :return: URL to article PDF.
    """
    link_element = soup.find('a', attrs={'class': 'article-dl-pdf-link link-icon'})

    if link_element and link_element.has_attr('href'):
        relative_url = link_element['href']
        return relative_url
    else:
        raise _ScrapeException("Could not found PDF link in soup")


def _extract_paper_license(soup: BeautifulSoup) -> str:
    """
    Extracts license information.
    :param soup: HTML soup of detailed article page.
    :return: License information.
    """
    span = soup.find('span', {'class': 'license-type'})

    if span:
        try:
            return span.find('a').text
        except AttributeError:
            if 'CC0' in span.text:
                return 'CC0'
            else:
                raise _ScrapeException("Could not find license information in soup")
    else:
        span = soup.find('span', {'class': 'license-type-none'})
        if span:
            return 'no reuse'
        else:
            raise _ScrapeException("Could not find license information in soup")


def _extract_withdrawn_information(soup: BeautifulSoup, paperhost: str) -> bool:
    """
    Checks whether the article is withdrawn or not.
    :param soup: HTML soup of detailed article page.
    :param paperhost: Lowercase paperhost name, either biorxiv or medrxiv.
    :return: True, if the article was withdrawn.
    """
    article_type_span = soup.find('span', {'class': f'{paperhost}-article-type'})

    if not article_type_span:
        return False

    return article_type_span.text.strip() == 'Withdrawn'


def _update_detailed_information(db_article: Paper) -> None:
    """
    Given a DB article object and an article URL, detailed information from the articles detail page are extracted.
    The log function is used for log output.

    :param db_article: DB article object.
    :return: True, if article was updated.
    """
    response = requests.get(db_article.url)

    # Extract version number
    redirected_url = response.url
    version_match = re.match(r'^\S+v(\d+)$', redirected_url)
    if version_match:
        article_version = version_match.group(1)
    else:
        raise _ScrapeException(f"Could not extract version number from article")
    db_article.version = article_version

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract license information
    db_article.license = _extract_paper_license(soup)

    # Extract PDF link to article
    db_article.pdf_url = db_article.host.url + _extract_relative_pdf_url(soup)

    # Extract category of article
    db_article.category = _extract_category(soup)

    # Extract withdrawn information
    db_article.withdrawn = _extract_withdrawn_information(soup, db_article.host.name.lower())

    db_article.save()  # Has to be saved before adding authors to create (empty) authors list

    # Extract authors information
    authors = _extract_authors_information(soup)
    db_article.authors.clear()
    for author in authors:
        db_article.authors.add(author)

    # Add time stamp and commit article to DB
    db_article.last_scrape = timezone.now()
    db_article.save()


def _get_or_create_article(
        article: Dict[str, str], update_unknown_category: bool) -> Tuple[bool, bool]:
    """
    Gets or create a DB article object.

    :param article: Article information, extracted from medRxiv JSON.
    :param update_unknown_category: If true, the detailed information of all articles with category 'Unkown' are
    updated.
    :return: First bool is True, iff article object was created, second one is True, if already existing article object
    was updated.
    """
    try:
        db_article = Paper.objects.get(doi=article['rel_doi'])

        if db_article.category_id.lower() == 'unknown' and update_unknown_category:
            _update_detailed_information(db_article)
            return False, True
        else:
            return False, False
    except Paper.DoesNotExist:
        db_article = Paper(
            doi=article['rel_doi']
        )

        db_article.title = article['rel_title']
        db_article.url = article['rel_link']
        db_article.abstract = article['rel_abs']
        db_article.published_at = article['rel_date']
        db_article.host = _get_or_create_paperhost(article['rel_site'])

        _update_detailed_information(db_article)

        return True, False


def scrape_articles(update_unknown_category: bool = True, log_function: Callable[[Any], Any] = print) -> None:
    """
    Scrapes all new articles from medRxiv/bioRxiv.

    :param update_unknown_category: If true, the detailed information of all articles with category 'Unkown' are
    updated.
    :param log_function: Function, called for logging output.
    """
    article_json = _get_article_json()

    n_created = 0
    n_updated = 0
    n_errors = 0

    start = timer()

    for article in article_json:
        doi = article['rel_doi']
        try:
            modify_status = _get_or_create_article(article, update_unknown_category)
        except _ScrapeException as ex:
            # Article is not created, if the PDF URL is not available.
            log_function(f"Failed to scrape article {doi}: {ex.msg}")
            n_errors += 1
            continue

        if modify_status[0]:
            log_function(f"Created DB record for {doi}")
            n_created += 1
        elif modify_status[1]:
            log_function(f"Updated DB record for {doi}")
            n_updated += 1
        else:
            log_function(f"Skipped article {doi}")

    end = timer()
    elapsed = timedelta(seconds=end-start)

    log_function(f"Created/Updated: {n_created}/{n_updated}")
    log_function(f"Elapsed time (total/per article): {elapsed}/{elapsed/(n_created+n_updated+n_errors)}")
    if n_errors > 0:
        log_function(f"Finished with {n_errors} errors")
        raise Exception


def update_articles(count: int = None, log_function: Callable[[Any], Any] = print):
    """
    Update detailed article information in DB.

    :param count: Number of article updates, begin with earliest updated ones.
    :param log_function: Function, called for logging output.
    """
    n_updated = 0
    n_errors = 0

    start = timer()

    articles = Paper.objects.all().order_by('last_scrape')
    if count:
        articles = articles[:count]

    for article in articles:
        try:
            _update_detailed_information(article)
            n_updated += 1
            log_function(f"Updated article {article.doi}")
        except _ScrapeException as ex:
            n_errors += 1
            log_function(f"Failed to update article {article.doi}: {ex.msg}")

    end = timer()
    elapsed = timedelta(seconds=end-start)

    log_function(f"Updated {n_updated} articles")
    log_function(f"Elapsed time (total/per article): {elapsed}/{elapsed/(n_updated+n_errors)}")
    if n_errors > 0:
        log_function(f"Finished with {n_errors} errors")
        raise Exception


def delete_revoked_articles(log_function: Callable[[Any], Any] = print) -> List[str]:
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
