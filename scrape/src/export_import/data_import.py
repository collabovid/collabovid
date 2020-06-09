import json
import tarfile
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO
from timeit import default_timer as timer

from data.models import (
    Author,
    Category,
    CategoryMembership,
    DataSource,
    Journal,
    Paper,
    PaperData,
    PaperHost
)
from django.utils.timezone import make_aware
from PIL import Image


class DataImport:
    @staticmethod
    def import_data(filepath, log=print):
        """Imports database data from .tar.gz archive to database."""

        start = timer()

        JOURNAL_NAME_MAX_LEN = Journal.max_length("name")
        PAPER_TITLE_MAX_LEN = Paper.max_length("title")
        AUTHOR_FIRSTNAME_MAX_LEN = Author.max_length("first_name")
        AUTHOR_LASTNAME_MAX_LEN = Author.max_length("last_name")

        with tarfile.open(filepath) as tar:
            with tar.extractfile("data.json") as f:
                data = json.load(f)

            journals = "journals" in data

            # Backward compatibility: only import the new ML-categories, not the old medrxiv ones.
            categories_ml = "categories_ml" in data

            # JSON dict keys are always strings, cast back to integers
            data["authors"] = {int(k): v for k, v in data["authors"].items()}
            data["paperhosts"] = {int(k): v for k, v in data["paperhosts"].items()}

            if journals:
                data["journals"] = {int(k): v for k, v in data["journals"].items()}

            paperhost_mapping = {}
            paperhosts_to_create = []
            for id, paperhost in data["paperhosts"].items():
                try:
                    db_paperhost = PaperHost.objects.get(name=paperhost["name"])
                except PaperHost.DoesNotExist:
                    db_paperhost = PaperHost(name=paperhost["name"])
                    paperhosts_to_create.append(db_paperhost)
                paperhost_mapping[id] = db_paperhost
            PaperHost.objects.bulk_create(paperhosts_to_create)

            journal_mapping = {}
            journals_to_create = []
            if journals:
                for id, journal in data["journals"].items():
                    try:
                        db_journal = Journal.objects.get(name=journal["name"][:JOURNAL_NAME_MAX_LEN])
                    except Journal.DoesNotExist:
                        db_journal = Journal(name=journal["name"][:JOURNAL_NAME_MAX_LEN])
                        journals_to_create.append(db_journal)
                    journal_mapping[id] = db_journal
                Journal.objects.bulk_create(journals_to_create)

            category_mapping = {}
            categories_to_create = []
            if categories_ml:
                for identifier, category in data["categories_ml"].items():
                    try:
                        db_category = Category.objects.get(model_identifier=identifier)
                    except Category.DoesNotExist:
                        db_category = Category(model_identifier=identifier, name=category["name"],
                                               description=category["description"], color=category["color"])
                        categories_to_create.append(db_category)
                    category_mapping[identifier] = db_category
                Category.objects.bulk_create(categories_to_create)

            paperdata_mapping = defaultdict()
            paperdata_to_create = []
            for i, paper in enumerate(data["papers"]):
                if not paper["published_at"]:
                    continue
                if paper["content"] and paper["content"] != "None":
                    db_paperdata = PaperData(content=paper["content"])
                    paperdata_mapping[paper["doi"]] = db_paperdata
                    paperdata_to_create.append(db_paperdata)
            PaperData.objects.bulk_create(paperdata_to_create)

            authors_created = 0
            papers_w_new_category = 0
            papers_to_add = []
            category_memberships_to_create = []
            doi_to_author_mapping = {}  # maps doi to list of db_authors for later insertion into m2m through table
            db_author_mapping = {}  # maps tuple (first name, last name) to dict:
                                    # {"db_author": db_author, "created": True / False}

            for i, paper in enumerate(data["papers"]):
                if i % 1000 == 0:
                    log(i)

                if not paper["published_at"]:
                    log(f"Not importing {paper['doi']} because the date is missing.")
                    continue

                update = True
                try:
                    db_paper = Paper.objects.get(doi=paper["doi"])
                    if DataSource.compare(db_paper.data_source_value, paper["datasource_id"]) >= 0:
                        update = False
                    else:
                        # delete db_paper and recreate -> easier to handle using bulk create
                        db_paper.delete()
                        db_paper = Paper(doi=paper["doi"])
                except Paper.DoesNotExist:
                    db_paper = Paper(doi=paper["doi"])

                if update:
                    db_paper.title = paper["title"][:PAPER_TITLE_MAX_LEN]
                    db_paper.abstract = paper["abstract"]
                    db_paper.data_source_value = paper["datasource_id"]
                    db_paper.version = paper["version"]
                    db_paper.covid_related = paper["covid_related"]
                    db_paper.url = paper["url"]
                    db_paper.pdf_url = paper["pdf_url"]
                    db_paper.is_preprint = paper["is_preprint"]
                    db_paper.published_at = paper["published_at"]

                    db_paper.last_scrape = make_aware(
                        datetime.strptime(paper["last_scrape"], "%Y-%m-%d %H:%M:%S")
                    ) if paper["last_scrape"] else None

                    db_paper.host = paperhost_mapping[paper["paperhost_id"]] if paper["paperhost_id"] else None
                    db_paper.pubmed_id = paper["pubmed_id"] if "pubmed_id" in paper else None
                    db_paper.journal = (
                        journal_mapping[paper["journal_id"]] if journals and paper["journal_id"] else None
                    )
                    db_paper.data = paperdata_mapping[db_paper.doi] if db_paper.doi in paperdata_mapping else None

                    img_path = paper["image"]
                    if img_path:
                        with tar.extractfile(img_path) as img_file:
                            image = Image.open(img_file)
                            buffer = BytesIO()
                            image.save(buffer, format="JPEG")
                            db_paper.add_preview_image(buffer, save=False)

                    papers_to_add.append(db_paper)

                    doi_to_author_mapping[db_paper.doi] = []  # maps doi to a list of its db_authors
                    for author_id in paper["author_ids"]:
                        author = data["authors"][author_id]
                        author_tuple = (author["firstname"][:AUTHOR_FIRSTNAME_MAX_LEN],
                                        author["lastname"][:AUTHOR_LASTNAME_MAX_LEN])
                        try:
                            db_author = Author.objects.get(first_name=author["firstname"][:AUTHOR_FIRSTNAME_MAX_LEN],
                                                           last_name=author["lastname"][:AUTHOR_LASTNAME_MAX_LEN])
                            db_author_mapping[author_tuple] = {"db_author": db_author, "created": False}
                        except Author.DoesNotExist:
                            if author_tuple in db_author_mapping:
                                # author was already requested earlier
                                db_author = db_author_mapping[author_tuple]["db_author"]
                            else:
                                db_author = Author(first_name=author["firstname"][:AUTHOR_FIRSTNAME_MAX_LEN],
                                    last_name=author["lastname"][:AUTHOR_LASTNAME_MAX_LEN])
                                db_author_mapping[author_tuple] = {"db_author": db_author, "created": True}
                                authors_created += 1
                        doi_to_author_mapping[db_paper.doi].append(db_author)

                if categories_ml and not db_paper.categories.exists():
                    # Set paper categories if they were not set (even on existing papers)
                    if paper["category_memberships"]:
                        papers_w_new_category += 1
                    for category in paper["category_memberships"]:
                        membership = CategoryMembership(paper=db_paper,
                                                        category=category_mapping[category["identifier"]],
                                                        score=category["score"])
                        category_memberships_to_create.append(membership)


            Paper.objects.bulk_create(papers_to_add)
            Author.objects.bulk_create([author["db_author"] for author in db_author_mapping.values()
                                        if author["created"]])
            CategoryMembership.objects.bulk_create(category_memberships_to_create)

            ThroughModel = Paper.authors.through
            ThroughModel.objects.bulk_create(
                [ThroughModel(paper_id=doi, author_id=author.pk) for doi, authors in doi_to_author_mapping.items()
                 for author in authors]
            )

        Author.cleanup()
        Journal.cleanup()
        PaperData.cleanup()

        end = timer()

        log(f"Finished import in {timedelta(seconds=end - start)}")
        log("Imported")
        log(f"\t{len(paperhosts_to_create)} paperhosts")
        log(f"\t{len(journals_to_create)} journals")
        log(f"\t{authors_created} authors")
        log(f"\t{len(categories_to_create)} ML categories")
        log(f"\t{len(papers_to_add)} papers")
        log(f"{papers_w_new_category} papers' categories were updated")
