import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'covid19_publications.settings'
import django

django.setup()

import json
import tarfile
from datetime import timedelta, datetime
from io import BytesIO
from timeit import default_timer as timer

from django.db import transaction
from django.utils.timezone import make_aware
from PIL import Image

from data.models import Author, Category, DataSource, Paper, PaperData, PaperHost


class UidDict(dict):
    """A dict with a specific ID field. Hashable."""

    def __init__(self, other, uid_key='id'):
        super().__init__(other)
        self.uid = uid_key

    def __hash__(self):
        return hash(self[self.uid])

    def __eq__(self, other):
        return self[self.uid] == other[self.uid]


class DataExporter:
    @staticmethod
    def export_data(queryset, output_directory='resources'):
        """Exports database data in json format and preview images to a tar.gz archive."""
        start = timer()

        datasources = set()
        authors = set()
        paperhosts = set()
        categories = set()
        papers = []

        tar = tarfile.open(f"{output_directory}/{datetime.strftime(datetime.now(), '%Y-%m-%d-%H%M')}.tar.gz", 'w:gz')

        for paper in queryset:
            if paper.data_source:
                datasources.add(UidDict({'id': paper.data_source.id, 'name': paper.data_source.name}))
            for author in paper.authors.all():
                authors.add(UidDict({
                    'id': author.pk,
                    'lastname': author.last_name,
                    'firstname': author.first_name,
                    'split_name': author.split_name,
                    'datasource_id': author.data_source_id,
                }))
            paperhosts.add(UidDict({'id': paper.host_id, 'name': paper.host.name}))
            if paper.category:
                categories.add(UidDict({'id': paper.category_id, 'name': paper.category.name}))
            papers.append({
                'doi': paper.doi,
                'title': paper.title,
                'abstract': paper.abstract,
                'author_ids': [author.pk for author in paper.authors.all()] if paper.authors else None,
                'content': paper.data.content if paper.data else None,
                'published_at': datetime.strftime(paper.published_at, '%Y-%m-%d') if paper.published_at else None,
                'category_id': paper.category.pk if paper.category else None,
                'paperhost_id': paper.host_id,
                'version': paper.version,
                'covid_related': paper.covid_related,
                'url': paper.url,
                'pdf_url': paper.pdf_url,
                'is_preprint': paper.is_preprint,
                'last_scrape': datetime.strftime(paper.last_scrape, '%Y-%m-%d %H:%M:%S') if paper.last_scrape else None,
                'image': paper.preview_image.name,
                'datasource_id': paper.data_source_id
            })
            if paper.preview_image and paper.preview_image.path:
                tar.add(paper.preview_image.path, arcname=paper.preview_image.name)

        data = {'datasources': list(datasources), 'categories': list(categories), 'authors': list(authors),
                'paperhosts': list(paperhosts), 'papers': papers}

        with open(f'{output_directory}/data.json', 'w') as file:
            json.dump(data, file)

        tar.add(f'{output_directory}/data.json', arcname='data.json')
        tar.close()

        os.remove(f'{output_directory}/data.json')

        end = timer()
        print(f"Finished export in {timedelta(seconds=end - start)}")

    @staticmethod
    def import_data(path):
        """Imports database data from .tar.gz archive to database."""
        start = timer()

        with tarfile.open(path) as tar:
            with tar.extractfile('data.json') as f:
                data = json.load(f)

            datasource_mapping = {}
            datasources_created = 0
            for datasource in data['datasources']:
                db_datasource, created = DataSource.objects.get_or_create(name=datasource['name'])
                datasource_mapping[datasource['id']] = db_datasource
                if created:
                    datasources_created += 1

            category_mapping = {}
            categories_created = 0
            for category in data['categories']:
                db_category, created = Category.objects.get_or_create(name=category['name'])
                category_mapping[category['id']] = db_category
                if created:
                    categories_created += 1

            paperhost_mapping = {}
            paperhosts_created = 0
            for paperhost in data['paperhosts']:
                db_paperhost, created = PaperHost.objects.get_or_create(name=paperhost['name'])
                paperhost_mapping[paperhost['id']] = db_paperhost
                if created:
                    paperhosts_created += 1

            author_mapping = {}
            authors_created = 0
            for i, author in enumerate(data['authors']):
                db_author, created = Author.objects.get_or_create(first_name=author['firstname'],
                                                                  last_name=author['lastname'])
                if created:
                    db_author.data_source = datasource_mapping[author['datasource_id']]
                    db_author.split_name = author['split_name']
                    db_author.save()
                    authors_created += 1

                author_mapping[author['id']] = db_author
                if i % 100 == 0:
                    print(f"Author progress: {i}/{len(data['authors'])}")

            papers_created = 0
            for i, paper in enumerate(data['papers']):
                if not Paper.objects.filter(doi=paper['doi']).exists():
                    db_paper = Paper(
                        doi=paper['doi'],
                        title=paper['title'],
                        abstract=paper['abstract'],
                        version=paper['version'],
                        covid_related=paper['covid_related'],
                        url=paper['url'],
                        pdf_url=paper['pdf_url'],
                        is_preprint=paper['is_preprint'],
                        last_scrape=make_aware(datetime.strptime(paper['last_scrape'], '%Y-%m-%d %H:%M:%S')) if paper[
                            'last_scrape'] else None,
                        published_at=paper['published_at'],
                        category=category_mapping[paper['category_id']] if paper['category_id'] else None,
                        data=PaperData.objects.create(content=paper['content']) if paper['content'] else None,
                        host=paperhost_mapping[paper['paperhost_id']] if paper['paperhost_id'] else None,
                        data_source=datasource_mapping[paper['datasource_id']]
                    )

                    with transaction.atomic():
                        db_paper.save()
                        for author_id in paper['author_ids']:
                            db_author = author_mapping[author_id]
                            db_paper.authors.add(db_author)

                        img_path = paper['image']
                        if img_path:
                            image = Image.open(tar.extractfile(img_path))
                            buffer = BytesIO()
                            image.save(buffer, format='JPEG')
                            db_paper.add_preview_image(buffer)
                        db_paper.save()
                    papers_created += 1

                if i % 100 == 0:
                    print(f"Paper progress: {i}/{len(data['papers'])}")

        end = timer()
        print(f"Finished in {timedelta(seconds=end - start)}")
        print(f"Imported {datasources_created} datasources, {paperhosts_created} paperhosts, {categories_created} "
              f"categories, {authors_created} authors and {papers_created} papers")


if __name__ == '__main__':
    exporter = DataExporter()
    exporter.export_data(Paper.objects.all())
