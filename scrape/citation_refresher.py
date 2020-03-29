import re
import html
import requests

from bs4 import BeautifulSoup
from django.utils import timezone

from data.models import Author


class CitationRefresher:
    def __init__(self):
        self.SUCCESS = 0
        self.NO_AUTHOR_FOUND = 1
        self.MULTIPLE_AUTHORS_FOUND = 2
        self.HTTP_ERROR = 3
        self.UNKNOWN = 4

    @staticmethod
    def escape(s: str) -> str:
        return html.escape(s).replace(' ', '%20')

    def get_scholar_citations(self, firstname: str, lastname: str):
        base_url = 'https://scholar.google.com/citations?view_op=search_authors&mauthors='
        url = f'{base_url}%22{self.escape(firstname)}+{self.escape(lastname)}%22'

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if response.status_code != 200:
            print(f"Request error: {response.status_code} ({response.reason})")
            return None, self.HTTP_ERROR

        authors = soup.find_all('div', {'class': 'gsc_1usr'})

        if len(authors) == 0:
            return None, self.NO_AUTHOR_FOUND

        if len(authors) > 1:
            return None, self.MULTIPLE_AUTHORS_FOUND

        for author in authors:
            citations_string = author.find('div', {'class': 'gs_ai_cby'}).text
            m = re.search(r'\d+$', citations_string)
            if m:
                citations = int(m.group())
                return citations, self.SUCCESS
            else:
                return None, self.NO_AUTHOR_FOUND

    @staticmethod
    def remove_shortened_names(name: str):
        final_name = ""
        names = name.split(" ")
        for name in names:
            if len(name) != 1:
                final_name += " " + name
        return final_name.strip()

    def refresh_citations(self, only_new=False, count=None):
        if only_new:
            authors = [a for a in Author.objects.all() if not a.citations_last_update]
        else:
            authors = Author.objects.all()

        if count:
            authors = sorted(authors, key=lambda a: a.citations_last_update)[0:count]

        for author in authors:
            citations, status = self.get_scholar_citations(author.first_name, author.last_name)

            if status == self.HTTP_ERROR:
                break

            author.citations_last_update = timezone.now()
            if status == self.SUCCESS:
                author.citation_count = citations
                author.save()
            elif status == self.NO_AUTHOR_FOUND:
                shortened_first_name = self.remove_shortened_names(author.first_name)
                if shortened_first_name != author.first_name:
                    citations, status = self.get_scholar_citations(shortened_first_name, author.last_name)
                    if status == self.SUCCESS:
                        author.citation_count = citations
                        author.save()
