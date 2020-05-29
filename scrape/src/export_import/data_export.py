import getpass
import io
import json
import os
import tarfile
from datetime import datetime, timedelta
from timeit import default_timer as timer

import requests
from django.conf import settings


class DataExport:
    @staticmethod
    def download_image(url):
        response = requests.get(url, stream=True)
        if not response.ok:
            return None
        else:
            return io.BytesIO(response.content)

    @staticmethod
    def export_data(queryset, out_dir, export_images=True, log=print):
        """Exports database data in json format and preview images to a tar.gz archive.
        Returns the path to the newly created archive."""
        start = timer()

        authors = {}
        paperhosts = {}
        categories = {}
        journals = {}
        papers = []

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        time = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M")
        filename = f"export_{getpass.getuser()}_{time}.tar.gz"
        path = f"{out_dir}/{filename}"
        json_path = f"{out_dir}/data.json"

        log(f"Create archive \"{path}\"")
        image_id_counter = 0
        try:
            with tarfile.open(path, "w:gz") as tar:
                for paper in queryset:
                    if paper.host_id not in paperhosts:
                        paperhosts[paper.host_id] = {"name": paper.host.name}

                    for author in paper.authors.all():
                        if author.pk not in authors:
                            authors[author.pk] = {
                                "lastname": author.last_name,
                                "firstname": author.first_name,
                            }

                    if paper.category and paper.category not in categories:
                        categories[paper.category_id] = {"name": paper.category.name}
                    if paper.journal and paper.journal not in journals:
                        journals[paper.journal_id] = {"name": paper.journal.name}

                    paper_data = {
                        "doi": paper.doi,
                        "title": paper.title,
                        "abstract": paper.abstract,
                        "author_ids": [author.pk for author in paper.authors.all()]
                        if paper.authors
                        else None,
                        "content": paper.data.content if paper.data else None,
                        "published_at": datetime.strftime(paper.published_at, "%Y-%m-%d")
                        if paper.published_at
                        else None,
                        "category_id": paper.category.pk if paper.category else None,
                        "paperhost_id": paper.host_id,
                        "version": paper.version,
                        "covid_related": paper.covid_related,
                        "url": paper.url,
                        "pdf_url": paper.pdf_url,
                        "is_preprint": paper.is_preprint,
                        "image": None,
                        "last_scrape": datetime.strftime(
                            paper.last_scrape, "%Y-%m-%d %H:%M:%S"
                        )
                        if paper.last_scrape
                        else None,
                        "datasource_id": paper.data_source_value,
                        "pubmed_id": paper.pubmed_id,
                        "journal_id": paper.journal.pk if paper.journal else None
                    }

                    if export_images and paper.preview_image and paper.preview_image.path:
                        image_path = f"thumbnails/{image_id_counter}.png"
                        if settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage':
                            tar.add(paper.preview_image.path, arcname=f"thumbnails/{image_id_counter}.png")
                            image_id_counter += 1
                            paper_data['image'] = image_path
                        elif settings.DEFAULT_FILE_STORAGE == 'storage.custom_storage.MediaStorage':
                            image = DataExport.download_image(paper.preview_image.name)
                            if image:
                                tarinfo = tarfile.TarInfo(name=f"thumbnails/{image_id_counter}.png")
                                tarinfo.size = len(image.getbuffer())
                                tar.addfile(tarinfo, fileobj=image)
                                image_id_counter += 1
                                paper_data['image'] = image_path

                    papers.append(paper_data)

                data = {
                    "categories": categories,
                    "authors": authors,
                    "paperhosts": paperhosts,
                    "papers": papers,
                    "journals": journals,
                }

                # json_io = io.BytesIO()
                # json.dump(data, json_io)
                #
                # tarinfo = tarfile.TarInfo(name='data.json')
                # tarinfo.size = len(json_io.getbuffer())
                # tar.addfile(tarinfo, fileobj=json_io)
                with open(json_path, "w") as file:
                    json.dump(data, file)

                tar.add(json_path, arcname="data.json")
        except Exception as ex:
            # Remove tar archive, if export was not successful
            if os.path.exists(path):
                os.remove(path)

            raise ex
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)

        end = timer()

        log(f"Finished export in {timedelta(seconds=end - start)}")
        log("Exported")
        log(f"\t{len(categories)} categories")
        log(f"\t{len(paperhosts)} paperhosts")
        log(f"\t{len(authors)} authors")
        log(f"\t{len(papers)} articles")
        log(f"\t{image_id_counter} images")
        log("Archive size: {0} MB".format(round(os.stat(path).st_size / (1000 ** 2), 2)))

        return filename
