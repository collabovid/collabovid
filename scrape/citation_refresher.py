import re
import html
import requests

from bs4 import BeautifulSoup
from data.models import Author


class CitationRefresher:

    NO_AUTHOR_FOUND = -1
    MULTIPLE_AUTHORS_FOUND = -2
    TOO_MANY_REQUESTS = -429

    def escape(self, s: str) -> str:
        return html.escape(s).replace(' ', '%20')

    def get_scholar_citations(self, firstname: str, lastname: str):
        base_url = 'https://scholar.google.com/citations?view_op=search_authors&mauthors='
        url = f'{base_url}%22{self.escape(firstname)}+{self.escape(lastname)}%22'

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if response.status_code != 200:
            print(f"Request error: {response.status_code} ({response.reason})")
            return self.TOO_MANY_REQUESTS

        authors = soup.find_all('div', {'class': 'gsc_1usr'})

        if len(authors) == 0:
            print(f"Found no author profile for '{firstname} {lastname}' on Google Scholar")
            return self.NO_AUTHOR_FOUND

        if len(authors) > 1:
            print(f"Found multiple profiles ({len(authors)}) for '{firstname} {lastname}' on Google Scholar")
            return self.MULTIPLE_AUTHORS_FOUND

        for author in authors:
            citations_string = author.find('div', {'class': 'gs_ai_cby'}).text
            m = re.search(r'\d+$', citations_string)
            if m:
                citations = int(m.group())
                print(f"Found citations information ({citations}) for '{firstname} {lastname}' on Google Scholar")
                return citations
            else:
                print(f"Found no citations information for '{firstname} {lastname}' on Google Scholar")
                return self.NO_AUTHOR_FOUND


    def remove_shortened_names(self, name: str):
        final_name = ""
        names = name.split(" ")
        for name in names:
            if len(name) != 1:
                final_name += " " + name
        return final_name.strip()


    def refresh_citations(self):
        authors = Author.objects.all()

        for author in authors:
            if author.citation_count == Author.CITATIONS_NOT_SCRAPED:
                print(f"Trying to scrape citations of {author.first_name} {author.last_name}")

                citations = self.get_scholar_citations(author.first_name, author.last_name)
                if citations == self.TOO_MANY_REQUESTS:
                    print("Too many requests. Stopping..")
                    break

                elif citations == self.NO_AUTHOR_FOUND:
                    # try again with shortened name
                    shortened_first_name = self.remove_shortened_names(author.first_name)
                    if shortened_first_name != author.first_name:
                        citations = self.get_scholar_citations(shortened_first_name, author.last_name)
                        if citations < 0:
                            print(f"Name shortening did not help for {author.first_name} {author.last_name}")
                            author.citation_count = Author.CITATIONS_AUTHOR_NOT_FOUND
                        else:
                            print(f"Name shortening helped for {author.first_name} {author.last_name}")
                            author.citation_count = citations

                    else:
                        author.citation_count = Author.CITATIONS_AUTHOR_NOT_FOUND
                else:
                    author.citation_count = citations

                author.save()
                print(f"Scraped citations of {author.first_name} {author.last_name}: {author.citation_count}")
