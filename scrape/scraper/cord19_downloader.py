import csv
import json
import os
import re
import shutil
import tarfile
from datetime import datetime
from pathlib import Path

import requests
from django.utils.dateparse import parse_datetime

from data.models import Paper, DataSource, Author, PaperData, Journal, PaperHost

# TODO:
#   - Identify removed articles

_CORD19_DATA_SOURCE = 'cord19-dataset'

_CORD19_BASE_URL = 'https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/latest/{0}{1}'
_CORD19_METADATA = 'metadata'
_CORD19_SUBSETS = {
    'comm_use_subset',
    'noncomm_use_subset',
    'custom_license',
    'biorxiv_medrxiv',
}

_CORD19_DOWNLOAD_PATH = Path('resources/cord19_data')


def is_doi(text: str):
    _DOI_PATTERN = r'10.\d{4,9}/\S+'
    return re.fullmatch(_DOI_PATTERN, text)


def _download_metadata():
    """Downloads the metadata CSV file."""
    print("Download latest CORD19 metadata. This may take a few minutes.")
    url = _CORD19_BASE_URL.format(_CORD19_METADATA, '.csv')
    download = requests.get(url)
    decoded_content = download.content.decode('utf-8')
    # with (_CORD19_DOWNLOAD_PATH / 'metadata.csv').open('w') as file:
    #    file.write(decoded_content)
    return decoded_content


def _download_full_text_data():
    """Downloads the full text of all CORD19 articles."""
    print("Download latest CORD19 full text data. This may take a few (more) minutes.")

    # Remove data directory with old content first
    if os.path.exists(_CORD19_DOWNLOAD_PATH):
        shutil.rmtree(_CORD19_DOWNLOAD_PATH)
    os.makedirs(_CORD19_DOWNLOAD_PATH, exist_ok=True)

    for subset_suffix in _CORD19_SUBSETS:
        print(f"- {subset_suffix}")
        url = _CORD19_BASE_URL.format(subset_suffix, '.tar.gz')
        targz_path = _CORD19_DOWNLOAD_PATH / 'tmp.tar.gz'

        with requests.get(url, stream=True) as download_stream:
            with open(targz_path, 'wb') as file:
                shutil.copyfileobj(download_stream.raw, file)

        tar = tarfile.open(targz_path, 'r:gz')
        tar.extractall(path=_CORD19_DOWNLOAD_PATH)
        tar.close()


def _contain_covid_keyword(db_article):
    _COVID19_KEYWORDS = r'(?:covid[ -]?19|sars[ -]?cov[ -]?2)'

    return re.match(_COVID19_KEYWORDS, db_article.title, re.IGNORECASE) \
           or re.match(_COVID19_KEYWORDS, db_article.abstract) \
           or (db_article.data and re.match(_COVID19_KEYWORDS, db_article.data.content))


def _get_json_path(article):
    path = Path(_CORD19_DOWNLOAD_PATH) / article['full_text_file']

    if article['has_pdf_parse']:
        path /= 'pdf_json'
    elif article['has_pmc_xml_parse']:
        path /= 'pmc_json'
    else:
        return None

    path /= f"{article['sha']}.json"

    if os.path.exists(path):
        return path
    else:
        return None


def _get_url(article):
    if article['pubmed_id']:
        return f"https://www.ncbi.nlm.nih.gov/pubmed/{article['pubmed_id']}/"
    if article['pmcid']:
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{article['pmcid']}/"
    # return None
    return "TUTO NULLO"


def _get_pdf_url(article):
    if article['url'].endswith('.pdf'):
        return article['url']
    # return None
    return "TUTO NULLO"


def update_cord19_data(log_function=print):
    metadata = _download_metadata()
    # _download_full_text_data()

    n_errors = 0
    n_already_tracked = 0

    lines = metadata.splitlines()
    header = lines[0].split(',')
    reader = csv.reader(lines[1:], delimiter=',')
    for row in reader:
        article = {k: v for (k, v) in zip(header, row)}

        if not (article['doi'] and is_doi(article['doi'])):
            log_function(f"Article \"{article['title']}\" from {article['source_x']} has no valid doi: "
                         f"{article['doi']}")
            n_errors += 1
            continue

        doi = article['doi']

        try:
            db_article = Paper.objects.get(doi=doi)
        except Paper.DoesNotExist:
            db_article = Paper(doi=doi)

        if db_article.data_source and db_article.data_source.name != _CORD19_DATA_SOURCE:
            log_function(f"Article is already tracked by {db_article.data_source.name}")
            n_already_tracked += 1

        db_article.url = _get_url(article)
        db_article.pdf_url = _get_pdf_url(article)
        db_article.title = article['title']
        db_article.abstract = article['abstract']
        db_article.host, _ = PaperHost.objects.get_or_create(name=article['source_x'], url='Peter')  # TODO
        db_article.journal, _ = Journal.objects.get_or_create(name=article['journal'])

        try:
            published_at = datetime.strptime(article['publish_time'], '%Y-%m-%d')
        except ValueError:
            published_at = datetime(year=1900, month=1, day=1)  # TODO
        db_article.published_at = published_at

        db_data_source, _ = DataSource.objects.get_or_create(name=_CORD19_DATA_SOURCE)
        db_article.data_source = db_data_source
        db_article.save()

        authors = [f"{name},".split(',') for name in article['authors'].split(';') if name]  # Add a further ',',
        # to ensure
        # to the name, to ensure that the name consists of at least two comma seperated values (lastname, firstname)
        if len(authors) != 0:
            db_article.authors.clear()
        for author in authors:
            try:
                db_author, created = Author.objects.get_or_create(
                    first_name=author[1],
                    last_name=author[0],
                    data_source=db_data_source,
                )
                db_author.save()
                db_article.authors.add(db_author)
            except IndexError:
                pass  # TODO

        json_path = _get_json_path(article)
        if json_path and os.path.exists(json_path):
            with json_path.open('r') as file:
                content = '\n'.join([paragraph['text'] for paragraph in json.load(file)['body_text']])
            if db_article.data:
                db_article.data.content = content
            else:
                db_content = PaperData.objects.create(content=content)
                db_article.data = db_content

        covid_related = _contain_covid_keyword(db_article)
        db_article.covid_related = covid_related
        db_article.save()

    # shutil.rmtree(_CORD19_DOWNLOAD_PATH)
