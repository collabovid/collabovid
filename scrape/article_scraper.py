from tasks import Runnable, register_task
from bs4 import BeautifulSoup
from data.models import PaperHost, Category, Paper, Author
import json
import requests
from typing import List, Tuple


@register_task
class ArticleScraper(Runnable):

    @staticmethod
    def task_name():
        return "scrape-articles"

    def __init__(self, update_unknown_category: bool, *args, **kwargs):
        super(ArticleScraper, self).__init__(*args, **kwargs)
        self._update_unknown_category = update_unknown_category

    def run(self):
        biorxiv_corona_json = 'https://connect.biorxiv.org/relate/collection_json.php?grp=181'

        try:

            response = requests.get(biorxiv_corona_json)
        except requests.exceptions.ConnectionError:
            self.log("Got connection error!")
            raise
            return

        data = json.loads(response.text)['rels']

        self.log("Scrape new papers")
        new_articles = 0
        skipped_articles = 0

        for i, item in enumerate(data):
            if item and self.scrape_item(item):
                new_articles += 1
                self.log("Scraped", i)
            else:
                skipped_articles += 1

        self.log(f"Skipped {skipped_articles} old article(s).")
        self.log(f"Scraped new papers successfully: {new_articles} new article(s)")

    def scrape_item(self, item):
        site = item['rel_site']
        if site == "medrxiv":
            name = "medRxiv"
        elif site == "biorxiv":
            name = "bioRxiv"
        else:
            name = site
        host, created = PaperHost.objects.get_or_create(
            name=name,
            url=f'https://www.{site}.org',
        )
        host.save()

        try:
            paper = Paper.objects.get(
                doi=item['rel_doi']
            )
            if paper.category_id == 'unknown' and self._update_unknown_category:
                url = item['rel_link']
                authors, category = self.get_detailed_information(url)

                db_category, created = Category.objects.get_or_create(
                    name=category,
                )
                db_category.save()

                paper.category = db_category
                paper.save()

            return False
        except Paper.DoesNotExist:
            paper = Paper(
                doi=item['rel_doi']
            )

            paper.title = item['rel_title']
            paper.url = item['rel_link']
            paper.abstract = item['rel_abs']
            paper.host = host
            paper.published_at = item['rel_date']

            pdf_url = self.extract_pdf_url(item['rel_link'], host)

            if pdf_url:
                paper.pdf_url = pdf_url
            else:
                return False

            url = item['rel_link']
            authors, category = self.get_detailed_information(url)

            db_category, created = Category.objects.get_or_create(
                name=category,
            )
            db_category.save()

            paper.category = db_category
            paper.save()

            for author in authors:
                db_author, created = Author.objects.get_or_create(
                    first_name=author[0],
                    last_name=author[1],
                )
                db_author.save()
                paper.authors.add(db_author)

            paper.save()

        return True

    def get_detailed_information(self, url: str) -> Tuple[List[Tuple[str, str, bool]], str]:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
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
                self.log(f"Ignore collaboration group: {author_webelement.text}")

        categories = soup.find_all('span', {'class': 'highwire-article-collection-term'})
        if len(categories) > 1:
            self.log(f"Found multiple categories")
        if len(categories) == 0:
            category = "unknown"
        else:
            category = categories[0].text.strip()
        return authors, category

    def extract_pdf_url(self, url: str, host: PaperHost):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        dl_element = soup.find('a', attrs={'class': 'article-dl-pdf-link link-icon'})

        if dl_element and dl_element.has_attr('href'):
            relative_link = dl_element['href']
            complete_url = host.url + relative_link
            return complete_url
        else:
            return None
