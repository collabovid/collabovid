import re
from django.utils import timezone
from time import sleep

import django
import requests
import html
from bs4 import BeautifulSoup

django.setup()

from data.models import Author


def escape(s: str) -> str:
    return html.escape(s).replace(' ', '%20')


def get_scholar_citations(firstname: str, lastname: str):
    base_url = 'https://scholar.google.com/citations?view_op=search_authors&mauthors='
    url = f'{base_url}%22{escape(firstname)}+{escape(lastname)}%22'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    if response.status_code != 200:
        print(f"Request error: {response.status_code} ({response.reason})")
        return None

    authors = soup.find_all('div', {'class': 'gsc_1usr'})

    if len(authors) == 0:
        print(f"Found no author profile for '{firstname} {lastname}' on Google Scholar")
        return None

    if len(authors) > 1:
        print(f"Found multiple profiles ({len(authors)}) for '{firstname} {lastname}' on Google Scholar")
        return None

    for author in authors:
        citations_string = author.find('div', {'class': 'gs_ai_cby'}).text
        m = re.search(r'\d+$', citations_string)
        if m:
            citations = int(m.group())
            print(f"Found citations information ({citations}) for '{firstname} {lastname}' on Google Scholar")
            return citations
        else:
            print(f"Found no citations information for '{firstname} {lastname}' on Google Scholar")
            return None


if __name__ == '__main__':
    authors = Author.objects.all()

    for i, author in enumerate(authors):
        if author.citation_count == -1:
            author.citation_count = None
            author.save()

        if author.citations_last_update == None:
            citations = get_scholar_citations(author.first_name, author.last_name)
            author.citations_last_update = timezone.now()
            if citations:
                author.citation_count = citations
            author.save()
            sleep(5)