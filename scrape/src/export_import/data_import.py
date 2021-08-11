import json
import tarfile
from datetime import datetime, timedelta
from io import BytesIO
from timeit import default_timer as timer

from django.db import transaction

from data.models import (
    Author,
    AuthorNameResolution,
    AuthorPaperMembership,
    Category,
    CategoryMembership,
    DataSource,
    DeleteCandidate,
    GeoCity,
    GeoCountry,
    GeoLocation,
    GeoLocationMembership,
    GeoNameResolution,
    IgnoredPaper,
    Journal,
    Paper,
    PaperData,
    PaperHost
)
from django.utils.timezone import make_aware
from PIL import Image
from tasks.colors import Red


class ImportMappings:
    """
    Helper class for data import.
    Mappings usually map the id (primary key that is read from export file) to the corresponding database object.
    """

    def __init__(self):
        self.journal_mapping = {}
        self.paperhost_mapping = {}
        self.category_mapping = {}
        self.location_mapping = {}
        self.paperdata_mapping = {}  # maps doi to PaperData
        self.doi_to_author_mapping = {}  # maps doi to list of db_authors for later insertion into m2m through table
        self.db_author_mapping = {}  # maps tuple (first name, last name) to dict:
        # {"db_author": db_author, "created": True / False}


class ImportStatistics:
    """
    Helper class that holds statistics of imported data.
    """

    def __init__(self):
        self.journals_created = 0
        self.paperhosts_created = 0
        self.categories_created = 0
        self.countries_created = 0
        self.cities_created = 0
        self.authors_created = 0
        self.papers_w_new_category = 0
        self.papers_w_new_location = 0
        self.added_papers = 0
        self.geo_name_resolutions_created = 0
        self.ignored_papers_created = 0
        self.delete_candidates_created = 0
        self.author_resolutions_created = 0

        self.authors_deleted = 0
        self.journals_deleted = 0
        self.paperdata_deleted = 0

        self.start = None
        self.end = None

    def __str__(self):
        s = []

        s.append(f"Finished import in {timedelta(seconds=self.end - self.start)}")
        s.append("Imported")
        s.append(f"\t{self.paperhosts_created} paperhosts")
        s.append(f"\t{self.journals_created} journals")
        s.append(f"\t{self.authors_created} authors")
        s.append(f"\t{self.categories_created} ML categories")
        s.append(f"\t{self.added_papers} papers")
        s.append(f"\t{self.countries_created} countries")
        s.append(f"\t{self.cities_created} cities")
        s.append(f"\t{self.geo_name_resolutions_created} geo name resolutions")
        s.append(f"\t{self.ignored_papers_created} papers to ignore list")
        s.append(f"\t{self.delete_candidates_created} delete candidates")
        s.append(f"\t{self.author_resolutions_created} author name resolutions")
        s.append(f"{self.papers_w_new_category} papers' categories were updated")
        s.append(f"{self.papers_w_new_location} papers' locations were updated")

        s.append(f"")
        s.append("Cleanup deleted")
        s.append(f"\t{self.authors_deleted} authors")
        s.append(f"\t{self.journals_deleted} journals")
        s.append(f"\t{self.paperdata_deleted} paperdata")
        return '\n'.join(s)

    def start_timer(self):
        self.start = timer()

    def stop_timer(self):
        self.end = timer()


class DataImport:
    """
    Import article data that has been previously exported using the DataExport class.
    """

    def __init__(self, log=print, progress=None):
        self._mappings = ImportMappings()
        self.log = log
        self.export_version = 0
        self.progress = progress if progress else lambda *args, **kwargs: args[0]
        self.statistics = ImportStatistics()

    def _cleanup_models(self):
        """
        Cleanup and remove orphaned entries from the database that may occur.
        """
        self.statistics.authors_deleted = Author.cleanup()
        self.statistics.journals_deleted = Journal.cleanup()

    def _import_journals(self, journals):
        """
        Import journals and build mapping of journal id (pk from export) to (possibly created)
        database journal object.
        """
        journal_name_max_len = Journal.max_length("name")
        journals_to_create = []
        for id, journal in journals.items():
            try:
                db_journal = Journal.objects.get(name=journal["name"][:journal_name_max_len])
            except Journal.DoesNotExist:
                db_journal = Journal(name=journal["name"][:journal_name_max_len])
                journals_to_create.append(db_journal)
            self._mappings.journal_mapping[id] = db_journal
        Journal.objects.bulk_create(journals_to_create)
        self.statistics.journals_created = len(journals_to_create)

    def _import_paperhosts(self, paperhosts):
        """
        Import paperhosts and build mapping of paperhost id (pk from export) to (possibly created)
        database paperhost object.
        """
        paperhosts_to_create = []
        for id, paperhost in paperhosts.items():
            try:
                db_paperhost = PaperHost.objects.get(name=paperhost["name"])
            except PaperHost.DoesNotExist:
                db_paperhost = PaperHost(name=paperhost["name"])
                paperhosts_to_create.append(db_paperhost)
            self._mappings.paperhost_mapping[id] = db_paperhost
        PaperHost.objects.bulk_create(paperhosts_to_create)
        self.statistics.paperhosts_created = len(paperhosts_to_create)

    def _import_categories(self, categories):
        """
        Import categories and build mapping of category id (model identifier from export) to (possibly created)
        database category object.
        """
        categories_to_create = []
        for identifier, category in categories.items():
            try:
                db_category = Category.objects.get(model_identifier=identifier)
            except Category.DoesNotExist:
                db_category = Category(model_identifier=identifier, name=category["name"],
                                       description=category["description"], color=category["color"])
                categories_to_create.append(db_category)
            self._mappings.category_mapping[identifier] = db_category
        Category.objects.bulk_create(categories_to_create)
        self.statistics.categories_created = len(categories_to_create)

    def _import_locations(self, locations):
        """
        Import locations and build mapping of location id (pk from export) to (possibly created)
        database location object.
        """

        # Create countries first, because cities reference a country in foreign key
        # Note: Bulk-Create is not possible with inheritance of models. So we create them one by one
        # but in one transaction (for the speed).
        with transaction.atomic():
            countries = {id: location for id, location in locations.items()
                         if location["type"] == "country"}
            cities = {id: location for id, location in locations.items()
                      if location["type"] == "city"}

            for id, country in countries.items():
                try:
                    db_country = GeoCountry.objects.get(geonames_id=country["geonames_id"])
                except GeoCountry.DoesNotExist:
                    db_country = GeoCountry(geonames_id=country["geonames_id"], name=country["name"],
                                            alias=country["alias"], latitude=country["latitude"],
                                            longitude=country["longitude"], alpha_2=country["alpha_2"])
                    self.statistics.countries_created += 1
                    db_country.save()

                self._mappings.location_mapping[id] = db_country

            for id, city in cities.items():
                try:
                    db_city = GeoCity.objects.get(geonames_id=city["geonames_id"])
                except GeoCity.DoesNotExist:
                    db_city = GeoCity(geonames_id=city["geonames_id"], name=city["name"], alias=city["alias"],
                                      latitude=city["latitude"], longitude=city["longitude"],
                                      country=self._mappings.location_mapping[city["country_id"]])
                    self.statistics.cities_created += 1
                    db_city.save()
                except GeoCity.MultipleObjectsReturned:
                    self.log(Red(city["name"] + " is saved multiple times"))

                self._mappings.location_mapping[id] = db_city

    def _import_paperdata(self, papers, paper_informations):
        """
        Import paperdata and build mapping of paper doi to (possibly created)
        database paperdata object.
        """
        paperdata_to_create = []
        for i, (paper, paper_info) in enumerate(zip(papers, paper_informations)):
            if not (paper_info["db_paper"] and paper_info["will_update"]):
                continue
            db_paperdata = PaperData(content=paper["content"], abstract=paper["abstract"])
            self._mappings.paperdata_mapping[paper["doi"]] = db_paperdata
            paperdata_to_create.append(db_paperdata)
        PaperData.objects.bulk_create(paperdata_to_create, batch_size=1000)
        self.statistics.paperdata_created = len(paperdata_to_create)

    def _import_geo_name_resolutions(self, geo_name_resolutions):
        """
        Import geo name resolutions. Does not overwrite, if source already exists in DB.
        """
        resolutions_to_create = []
        for resolution in geo_name_resolutions:
            if not GeoNameResolution.objects.filter(source_name=resolution["source_name"]).exists():
                resolutions_to_create.append(GeoNameResolution(source_name=resolution["source_name"],
                                                               target_geonames_id=resolution["target_geonames_id"]))
        GeoNameResolution.objects.bulk_create(resolutions_to_create)
        self.statistics.geo_name_resolutions_created = len(resolutions_to_create)

    def _import_paper_ignore_list(self, ignored_papers):
        """
        Import a list of dois that shall be ignored.
        Do not create in bulk, since we want to send post_save signals (to delete ignored papers, if present).
        """
        for doi in ignored_papers:
            ignored_paper, created = IgnoredPaper.objects.get_or_create(doi=doi)
            if created:
                self.statistics.ignored_papers_created += 1

    def _import_author_resolutions(self, author_resolutions):
        """
        Imports the author name resolutions.
        """
        for res in author_resolutions:
            if not res["target_lname"] and not res["target_fname"]:
                AuthorNameResolution.ignore(first=res["source_fname"], last=res["source_lname"])
                resolution_created = True
            else:
                resolution_created, _ = AuthorNameResolution.add(
                    old_first=res["source_fname"], old_last=res["source_lname"],
                    new_first=res["target_fname"], new_last=res["target_lname"]
                )
            self.statistics.author_resolutions_created += int(resolution_created)

    def _compute_updatable_papers(self, papers):
        """
        Computes which of the papers from the import will be touched for (re-)creation and creates model instances
        (without saving), if necessary.
        Returns a list of dicts of size len(papers) of format {db_paper, will_update}.
        db_paper=None indicates an error (possibly with the publication date), so the paper won't be created/updated.
        """
        paper_informations = []
        for i, paper in enumerate(papers):
            if not paper["published_at"]:
                self.log(f"Not importing {paper['doi']} because the date is missing.")
                paper_informations.append({"db_paper": None, "will_update": False})
                continue
            try:
                db_paper = Paper.objects.get(doi=paper["doi"])
                if DataSource.compare(db_paper.data_source_value, paper["datasource_id"]) >= 0:
                    paper_informations.append({"db_paper": db_paper, "will_update": False})
                    continue
                else:
                    # delete db_paper and recreate -> easier to handle using bulk create
                    db_paper.delete()
                    db_paper = Paper(doi=paper["doi"])
            except Paper.DoesNotExist:
                db_paper = Paper(doi=paper["doi"])
            paper_informations.append({"db_paper": db_paper, "will_update": True})
        return paper_informations

    def _import_papers(self, papers, paper_informations, authors,
                       import_locations, import_ml_categories, import_journals, tar):
        """
        Import papers and its associated authors. Also its relations with locations, categories and journals,
        depending on the bool parameters.
        The mapping of all things (except authors) must have been built before using this.
        """
        paper_title_max_len = Paper.max_length("title")
        author_firstname_max_len = Author.max_length("first_name")
        author_lastname_max_len = Author.max_length("last_name")

        papers_to_add = []
        category_memberships_to_create = []
        location_memberships_to_create = []

        for i, (paper, paper_info) in enumerate(zip(papers, paper_informations)):
            db_paper = paper_info["db_paper"]
            if not db_paper:
                continue

            if paper_info["will_update"]:
                db_paper.title = paper["title"][:paper_title_max_len]
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

                if self.export_version > 4:
                    db_paper.scrape_hash = paper["scrape_hash"]
                if self.export_version > 5:
                    db_paper.manually_modified = paper["manually_modified"]
                db_paper.host = self._mappings.paperhost_mapping[paper["paperhost_id"]] if paper[
                    "paperhost_id"] else None
                db_paper.pubmed_id = paper["pubmed_id"] if "pubmed_id" in paper else None
                db_paper.journal = (
                    self._mappings.journal_mapping[paper["journal_id"]] if import_journals and paper[
                        "journal_id"] else None
                )
                db_paper.data = self._mappings.paperdata_mapping[
                    db_paper.doi] if db_paper.doi in self._mappings.paperdata_mapping else None

                if self.export_version >= 4:
                    db_paper.visualized = paper["visualized"]
                    db_paper.vectorized = paper["vectorized"]

                img_path = paper["image"]
                if img_path:
                    with tar.extractfile(img_path) as img_file:
                        image = Image.open(img_file)
                        buffer = BytesIO()
                        image.save(buffer, format="JPEG")
                        db_paper.add_preview_image(buffer, save=False)

                papers_to_add.append(db_paper)
                self.statistics.added_papers += 1

                self._mappings.doi_to_author_mapping[db_paper.doi] = []

                for author_id in paper["author_ids"]:
                    author = authors[author_id]
                    author_tuple = (author["firstname"][:author_firstname_max_len],
                                    author["lastname"][:author_lastname_max_len])
                    try:
                        db_author = Author.objects.get(first_name=author["firstname"][:author_firstname_max_len],
                                                       last_name=author["lastname"][:author_lastname_max_len])
                        self._mappings.db_author_mapping[author_tuple] = {"db_author": db_author, "created": False}
                    except Author.DoesNotExist:
                        if author_tuple in self._mappings.db_author_mapping:
                            # author was already requested earlier
                            db_author = self._mappings.db_author_mapping[author_tuple]["db_author"]
                        else:
                            db_author = Author(first_name=author["firstname"][:author_firstname_max_len],
                                               last_name=author["lastname"][:author_lastname_max_len])
                            self._mappings.db_author_mapping[author_tuple] = {"db_author": db_author, "created": True}
                            self.statistics.authors_created += 1
                    self._mappings.doi_to_author_mapping[db_paper.doi].append(db_author)

            if import_ml_categories and not db_paper.categories.exists():
                # Set paper categories if they were not set (even on existing papers)
                if paper["category_memberships"]:
                    self.statistics.papers_w_new_category += 1
                for category in paper["category_memberships"]:
                    membership = CategoryMembership(paper=db_paper,
                                                    category=self._mappings.category_mapping[category["identifier"]],
                                                    score=category["score"])
                    category_memberships_to_create.append(membership)

            if import_locations and not db_paper.locations.exists():
                # Set paper locations if they were not set (even on existing papers)
                if paper["locations"]:
                    self.statistics.papers_w_new_location += 1
                    db_paper.location_modified = paper["location_modified"]
                for location in paper["locations"]:
                    membership = GeoLocationMembership(paper=db_paper,
                                                       location=self._mappings.location_mapping[location["id"]],
                                                       state=location["state"])
                    location_memberships_to_create.append(membership)

        Paper.objects.bulk_create(papers_to_add, batch_size=1000)
        Author.objects.bulk_create([author["db_author"] for author in self._mappings.db_author_mapping.values()
                                    if author["created"]], batch_size=1000)
        CategoryMembership.objects.bulk_create(category_memberships_to_create, batch_size=1000)
        GeoLocationMembership.objects.bulk_create(location_memberships_to_create, batch_size=1000)

        author_paper_memberships = []
        for doi, authors in self._mappings.doi_to_author_mapping.items():
            author_paper_memberships += [AuthorPaperMembership(paper_id=doi, author_id=author.pk, rank=i)
                                         for i, author in enumerate(authors)]
        AuthorPaperMembership.objects.bulk_create(author_paper_memberships, batch_size=1000)
        # recompute counts because post save signals are not triggered on bulk create
        GeoLocation.recompute_counts(GeoCity.objects.all(), GeoCountry.objects.all())

    def _import_delete_candidates(self, delete_candidates):
        """
        Imports the given delete candidates into the database.
        Should be called, after all papers from export have been imported.
        """
        candidates_to_create = []
        for candidate in delete_candidates:
            try:
                paper = Paper.objects.get(doi=candidate["doi"])
            except Paper.DoesNotExist:
                continue
            try:
                DeleteCandidate.objects.get(paper=paper, type=candidate["type"])
            except DeleteCandidate.DoesNotExist:
                candidates_to_create.append(DeleteCandidate(paper=paper, type=candidate["type"],
                                                            false_positive=candidate["fp"], score=candidate["score"]))
        DeleteCandidate.objects.bulk_create(candidates_to_create)
        self.statistics.delete_candidates_created = len(candidates_to_create)

    def import_data(self, filepath):
        """
        Imports database data from .tar.gz archive to database.
        """
        self.statistics.start_timer()
        self._mappings = ImportMappings()

        with tarfile.open(filepath) as tar:
            with tar.extractfile("data.json") as f:
                data = json.load(f)

            self.export_version = data["export_version"] if "export_version" in data else 0
            if not self.export_version:
                self.log("Export data does not contain version. Is the export too old? Aborting.")
                return

            self.log(f"Starting import of version {self.export_version}.")

            # Backward compatibility: only import the things that have been exported.
            import_journals = "journals" in data
            import_ml_categories = "categories_ml" in data
            import_locations = "locations" in data
            import_geo_name_resolutions = "geo_name_resolutions" in data

            # JSON dict keys are always strings, cast back to integers
            data["authors"] = {int(k): v for k, v in data["authors"].items()}
            data["paperhosts"] = {int(k): v for k, v in data["paperhosts"].items()}

            if import_journals:
                data["journals"] = {int(k): v for k, v in data["journals"].items()}
            if import_locations:
                data["locations"] = {int(k): v for k, v in data["locations"].items()}

            self._import_paperhosts(data["paperhosts"])
            print("progress 10")
            self.progress(10)

            if import_journals:
                self._import_journals(data["journals"])
                self.progress(15)
            if import_ml_categories:
                self._import_categories(data["categories_ml"])
                self.progress(20)
            if import_locations:
                self._import_locations(data["locations"])
                self.progress(25)
            if import_geo_name_resolutions:
                self._import_geo_name_resolutions(data["geo_name_resolutions"])
                self.progress(30)

            paper_information = self._compute_updatable_papers(data["papers"])

            self._import_paperdata(self.progress(data["papers"], proportion=0.2), paper_information)
            self._import_papers(self.progress(data["papers"], proportion=0.45), paper_information, data["authors"],
                                import_locations, import_ml_categories, import_journals, tar)

            if self.export_version > 1:
                self._import_paper_ignore_list(data["ignored_papers"])
                self._import_delete_candidates(data["delete_candidates"])

            if self.export_version > 2:
                self._import_author_resolutions(data["author_resolutions"])

        self.log("Starting cleanup")
        self._cleanup_models()

        self.statistics.stop_timer()
        self.log(self.statistics)
