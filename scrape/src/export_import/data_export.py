import getpass
import json
import os
import tarfile
from datetime import datetime, timedelta
from timeit import default_timer as timer


class DataExport:
    @staticmethod
    def export_data(queryset, out_dir, log=print):
        """Exports database data in json format and preview images to a tar.gz archive.
        Returns the path to the newly created archive."""
        start = timer()

        datasources = {}
        authors = {}
        paperhosts = {}
        categories = {}
        papers = []

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        time = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M")
        filename = f"dbexport_{getpass.getuser()}_{time}.tar.gz"
        path = f"{out_dir}/{filename}"

        log(f"Create archive \"{path}\"")
        with tarfile.open(path, "w:gz") as tar:
            for paper in queryset:
                if paper.data_source and paper.data_source_id not in datasources:
                    datasources[paper.data_source_id] = {"name": paper.data_source.name}

                if paper.host_id not in paperhosts:
                    paperhosts[paper.host_id] = {"name": paper.host.name}

                for author in paper.authors.all():
                    if author.pk not in authors:
                        authors[author.pk] = {
                            "lastname": author.last_name,
                            "firstname": author.first_name,
                            "split_name": author.split_name,
                            "datasource_id": author.data_source_id,
                        }

                if paper.category and paper.category not in categories:
                    categories[paper.category_id] = {"name": paper.category.name}

                papers.append(
                    {
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
                        "last_scrape": datetime.strftime(
                            paper.last_scrape, "%Y-%m-%d %H:%M:%S"
                        )
                        if paper.last_scrape
                        else None,
                        "image": paper.preview_image.name,
                        "datasource_id": paper.data_source_id,
                    }
                )

                if paper.preview_image and paper.preview_image.path:
                    tar.add(paper.preview_image.path, arcname=paper.preview_image.name)

            data = {
                "datasources": datasources,
                "categories": categories,
                "authors": authors,
                "paperhosts": paperhosts,
                "papers": papers,
            }

            json_path = f"{out_dir}/data.json"
            with open(json_path, "w") as file:
                json.dump(data, file)

            tar.add(json_path, arcname="data.json")

        os.remove(json_path)

        end = timer()

        log(f"Finished export in {timedelta(seconds=end - start)}")
        log("Exported")
        log(f"\t{len(datasources)} datasources")
        log(f"\t{len(categories)} categories")
        log(f"\t{len(paperhosts)} paperhosts")
        log(f"\t{len(authors)} authors")
        log(f"\t{len(papers)} articles")

        return filename
