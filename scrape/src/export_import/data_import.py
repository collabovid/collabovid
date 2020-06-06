import json
import tarfile
from datetime import datetime, timedelta
from io import BytesIO
from timeit import default_timer as timer

from data.models import Author, Journal, Paper, PaperData, PaperHost
from django.db import transaction
from django.utils.timezone import make_aware
from PIL import Image

#  TODO: Import new category data.
class DataImport:
    @staticmethod
    def import_data(filepath, log=print):
        """Imports database data from .tar.gz archive to database."""
        start = timer()

        with tarfile.open(filepath) as tar:
            with tar.extractfile("data.json") as f:
                data = json.load(f)

            journals = "journals" in data

            # JSON dict keys are always strings, cast back to integers
            data["authors"] = {int(k): v for k, v in data["authors"].items()}
            data["paperhosts"] = {int(k): v for k, v in data["paperhosts"].items()}

            if journals:
                data["journals"] = {int(k): v for k, v in data["journals"].items()}

            paperhost_mapping = {}
            paperhosts_created = 0
            for id, paperhost in data["paperhosts"].items():
                db_paperhost, created = PaperHost.objects.get_or_create(
                    name=paperhost["name"]
                )
                paperhost_mapping[id] = db_paperhost
                if created:
                    paperhosts_created += 1

            journal_mapping = {}
            journals_created = 0
            if journals:
                for id, journal in data["journals"].items():
                    db_journal, created = Journal.objects.get_or_create(
                        name=journal["name"][:Journal.max_length("name")]
                    )
                    journal_mapping[id] = db_journal
                    if created:
                        journals_created += 1

            papers_created = 0
            authors_created = 0
            for i, paper in enumerate(data["papers"]):
                if not Paper.objects.filter(doi=paper["doi"]).exists():
                    if not paper["published_at"]:
                        print(f"Not importing {paper['doi']} because the date is missing.")
                        continue
                    with transaction.atomic():
                        db_paper = Paper(
                            doi=paper["doi"],
                            title=paper["title"][:Paper.max_length("title")],
                            abstract=paper["abstract"],
                            version=paper["version"],
                            covid_related=paper["covid_related"],
                            url=paper["url"],
                            pdf_url=paper["pdf_url"],
                            is_preprint=paper["is_preprint"],
                            last_scrape=make_aware(
                                datetime.strptime(
                                    paper["last_scrape"], "%Y-%m-%d %H:%M:%S"
                                )
                            )
                            if paper["last_scrape"]
                            else None,
                            published_at=paper["published_at"],
                            data=PaperData.objects.create(content=paper["content"])
                            if paper["content"]
                            else None,
                            host=paperhost_mapping[paper["paperhost_id"]]
                            if paper["paperhost_id"]
                            else None,
                            data_source_value=paper["datasource_id"],
                            pubmed_id=paper["pubmed_id"]
                            if "pubmed_id" in paper
                            else None,
                            journal=journal_mapping[paper["journal_id"]]
                            if journals and paper["journal_id"]
                            else None,
                        )

                        db_paper.save()

                        for author_id in paper["author_ids"]:
                            author = data["authors"][author_id]
                            db_author, created = Author.objects.get_or_create(
                                first_name=author["firstname"][:Author.max_length("first_name")],
                                last_name=author["lastname"][:Author.max_length("last_name")],
                            )
                            if created:
                                authors_created += 1
                            db_paper.authors.add(db_author)

                        img_path = paper["image"]
                        if img_path:
                            with tar.extractfile(img_path) as img_file:
                                image = Image.open(img_file)
                                buffer = BytesIO()
                                image.save(buffer, format="JPEG")
                                db_paper.add_preview_image(buffer)
                        db_paper.save()
                    papers_created += 1

        end = timer()

        log(f"Finished import in {timedelta(seconds=end - start)}")
        log("Imported")
        log(f"\t{paperhosts_created} paperhosts")
        log(f"\t{journals_created} journals")
        log(f"\t{authors_created} authors")
        log(f"\t{papers_created} papers")
