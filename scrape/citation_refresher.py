import re
import html
import requests

from bs4 import BeautifulSoup
from django.utils import timezone

from data.models import Author
from tasks import Runnable

class CitationRefresher(Runnable):
    
    SUCCESS = 0
    NO_AUTHOR_FOUND = 1
    MULTIPLE_AUTHORS_FOUND = 2
    HTTP_ERROR = 3
    UNKNOWN = 4
    
    @staticmethod
    def task_name():
        return "refresh-citations"

    def __init__(self, only_new=False, count=None, *args, **kwargs):
        super(CitationRefresher, self).__init__(*args, **kwargs)

        self._only_new = only_new
        self._count = count

    def run(self):
        if self._only_new:
            authors = [a for a in Author.objects.all() if not a.citations_last_update]
        else:
            authors = Author.objects.all()

        if self._count:
            authors = sorted(authors, key=lambda a: a.citations_last_update)[0:self._count]

        for author in authors:
            citations, status = self.get_scholar_citations(author.first_name, author.last_name)

            if status == CitationRefresher.HTTP_ERROR:
                self.log("Encountered HTTP Error. Aborting")
                return

            author.citations_last_update = timezone.now()
            if status == CitationRefresher.SUCCESS:
                author.citation_count = citations
            elif status == CitationRefresher.NO_AUTHOR_FOUND:
                shortened_first_name = self.remove_shortened_names(author.first_name)
                if shortened_first_name != author.first_name:
                    citations, status = self.get_scholar_citations(shortened_first_name, author.last_name)
                    if status == CitationRefresher.SUCCESS:
                        author.citation_count = citations
            author.save()

        self.log("Finished Citation Refresh")

    @staticmethod
    def escape(s: str) -> str:
        return html.escape(s).replace(' ', '%20')

    def get_scholar_citations(self, firstname: str, lastname: str):
        base_url = 'https://scholar.google.com/citations?view_op=search_authors&mauthors='
        url = f'{base_url}%22{self.escape(firstname)}+{self.escape(lastname)}%22'

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if response.status_code != 200:
            self.log(f"Request error: {response.status_code} ({response.reason})")
            return None, CitationRefresher.HTTP_ERROR

        authors = soup.find_all('div', {'class': 'gsc_1usr'})

        if len(authors) == 0:
            return None, CitationRefresher.NO_AUTHOR_FOUND

        if len(authors) > 1:
            return None, CitationRefresher.MULTIPLE_AUTHORS_FOUND

        for author in authors:
            citations_string = author.find('div', {'class': 'gs_ai_cby'}).text
            m = re.search(r'\d+$', citations_string)
            if m:
                citations = int(m.group())
                return citations, CitationRefresher.SUCCESS
            else:
                return None, CitationRefresher.NO_AUTHOR_FOUND

    @staticmethod
    def remove_shortened_names(name: str):
        final_name = ""
        names = name.split(" ")
        for name in names:
            if len(name) > 2 or (len(name) == 2 and name[1] != '.'):
                final_name += " " + name
        return final_name.strip()

