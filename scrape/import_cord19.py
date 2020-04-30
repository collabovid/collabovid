import csv
import json
import os
import re
import shutil
import tarfile

import requests

from pathlib import Path

_CORD19_BASE_URL = 'https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/latest/{0}{1}'
_CORD19_METADATA = 'metadata'
_CORD19_SUBSETS = {
    'comm_use_subset',
    'noncomm_use_subset',
    'custom_license',
    'biorxiv_medrxiv',
}

_CORD19_DOWNLOAD_PATH = Path('resources/cord19_data')

_COVID19_KEYWORDS = r'(?:covid[ -]?19|sars[ -]?cov[ -]?2)'

_DOI_PATTERN = r'10.\d{4,9}/\S+'


def is_doi(text: str):
    return re.fullmatch(_DOI_PATTERN, text)


def _download_metadata():
    """Downloads the metadata CSV file."""
    print("Download latest CORD19 metadata. This may take a few minutes.")
    url = _CORD19_BASE_URL.format(_CORD19_METADATA, '.csv')
    download = requests.get(url)
    decoded_content = download.content.decode('utf-8')
    with (_CORD19_DOWNLOAD_PATH / 'metadata.csv').open('w') as file:
        file.write(decoded_content)
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

        os.remove(targz_path)


def _contain_covid_keyword(article):
    return re.match(_COVID19_KEYWORDS, article['title'], re.IGNORECASE) \
           or re.match(_COVID19_KEYWORDS, article['abstract'])


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


def update_cord19_data(log_function):
    n_errors = 0
    metadata = _download_metadata()

    lines = metadata.splitlines()
    header = lines[0]
    reader = csv.reader(lines[1:], delimiter=',')
    for row in reader:
        article = {k: v for (k, v) in zip(header, row)}

        if not (article['doi'] and is_doi(article['doi'])):
            log_function(f"Article \"{article['title']}\" from {article['source_x']} has no valid doi: "
                         f"{article['doi']}")
            n_errors += 1
            continue

        authors = [name.split(',') for name in article['authors'].split(';')]

        contain_covid_keywords = _contain_covid_keyword(article)

        json_path = _get_json_path(article)
        if json_path:
            with json_path.open('r') as file:
                content = '\n'.join([paragraph['text'] for paragraph in json.load(file)['body_text']])









if __name__ == '__main__':
    #_download_full_text_data()
    _download_metadata()