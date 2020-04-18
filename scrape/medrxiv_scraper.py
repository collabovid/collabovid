import json
import re

import requests
from bs4 import BeautifulSoup

from data.models import PaperHost, Paper, Author, Category

_COVID_JSON_URL = 'https://connect.medrxiv.org/relate/collection_json.php?grp=181'
_MEDRXIV_URL = 'https://www.medrxiv.org/content/{0}'
_BIORXIV_URL = 'https://www.biorxiv.org/content/{0}'


def _get_article_json():
    """
    Downloads the list of all COVID-19 related articles from medRxiv in JSON format.
    """
    try:
        response = requests.get(_COVID_JSON_URL)
        return json.loads(response.text)['rels']
    except requests.exceptions.ConnectionError as ex:
        raise Exception("Unable to download medRxiv COVID-19 article list JSON")


def _get_or_create_paperhost(name):
    if name == "medrxiv":
        paperhost = "medRxiv"
        url = 'https://www.medrxiv.org'
    elif name == "biorxiv":
        paperhost = "bioRxiv"
        url = 'https://www.biorxiv.org'
    else:
        paperhost = name
        url = None

    host, created = PaperHost.objects.get_or_create(
        name=paperhost,
        url=url,
    )
    if created:
        host.save()

    return host


def _extract_authors_information(soup):
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


def _extract_category(soup):
    categories = soup.find_all('span', {'class': 'highwire-article-collection-term'})
    if len(categories) == 0:
        return "unknown"
    else:
        return categories[0].text.strip()


class _PdfUrlNotFoundException(Exception):
    pass


def _extract_relative_pdf_url(soup):
    dl_element = soup.find('a', attrs={'class': 'article-dl-pdf-link link-icon'})

    if dl_element and dl_element.has_attr('href'):
        relative_url = dl_element['href']
        return relative_url
    else:
        raise _PdfUrlNotFoundException


def _update_detailed_information(db_article, article_url, log_function):
    response = requests.get(article_url)
    redirected_url = response.url

    version_match = re.match('^\S+v(\d+)$', redirected_url)
    if version_match:
        article_version = version_match.group(1)
    else:
        log_function(f'{db_article.doi}: Could not extract version')
        article_version = None

    soup = BeautifulSoup(response.text, 'html.parser')
    authors = _extract_authors_information(soup)
    category = _extract_category(soup)
    db_article.pdf_url = db_article.host.url + _extract_relative_pdf_url(soup)

    db_category, created = Category.objects.get_or_create(
        name=category,
    )
    db_category.save()
    db_article.category = db_category
    db_article.save() # Has to be saved before adding authors

    db_article.authors.clear()
    for author in authors:
        db_author, created = Author.objects.get_or_create(
            first_name=author[0],
            last_name=author[1],
        )
        db_author.save()
        db_article.authors.add(db_author)
    db_article.save()


def _get_or_create_article(article, update_unknown_category, log_function):
    try:
        db_article = Paper.objects.get(doi=article['rel_doi'])

        if db_article.category_id == 'Unknown' and update_unknown_category:
            _update_detailed_information(db_article, article['rel_link'], log_function)

        return False
    except Paper.DoesNotExist:
        db_article = Paper(
            doi=article['rel_doi']
        )

        db_article.title = article['rel_title']
        db_article.url = article['rel_link']
        db_article.abstract = article['rel_abs']
        db_article.published_at = article['rel_date']
        db_article.host = _get_or_create_paperhost(article['rel_site'])
        _update_detailed_information(db_article, article['rel_link'], log_function)

        return True

def scrape_articles(update_unknown_category=True, log_function=print):
    article_json = _get_article_json()
    count_created = 0
    count_updated = 0
    for article in article_json:
        doi = article['rel_doi']
        try:
            if _get_or_create_article(article, update_unknown_category, log_function):
                log_function(f"Created DB record for {doi}")
                count_created += 1
            elif update_unknown_category:
                log_function(f"Updated DB record for {doi}")
                count_updated += 1
            else:
                log_function(f"Skipped article {doi}")
        except _PdfUrlNotFoundException:
            log_function(f"Could not find PDF URL for {doi}, skip article")

    log_function(f"Created/Updated: {count_created}/{count_updated}")


def delete_revoked_articles():
    """
    Remove all revoked articles (no longer in JSON file) from DB.
    """
    json_dois = [article['rel_doi'] for article in _get_article_json()]
    revoked_articles = []
    for db_article in Paper.objects.all():
        if db_article.doi not in json_dois:
            revoked_articles.append(db_article)

    removed_articles = [article.doi for article in revoked_articles]
    for db_article in revoked_articles:
        db_article.delete()

    return removed_articles