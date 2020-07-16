from bibtexparser.bparser import BibTexParser
from django.db.models import Q, When, Case, TextField, Value
from elasticsearch_dsl import Q as QEs

from data.documents import PaperDocument
from data.models import Paper
import bibtexparser
from bibtexparser.customization import *


class LiteratureEntry:

    """
    This class is used to store a literature entry along with some important information
    on how the record was found.
    """

    def __init__(self, doi, title):
        self._doi = doi
        self._title = title
        self.result_found = False
        self.inexact_result_found = False

    @property
    def title(self):
        return self._title

    @property
    def doi(self):
        return self._doi


class LiteratureFileAnalyzer:
    """
    Base class for a literature file analyzer.
    """

    @staticmethod
    def load_entries_from_database(entries):
        search = PaperDocument.search()

        dois_for_entry = list()

        for entry in entries:
            query = None

            # Try to find record using its doi or full title

            if entry.doi:
                query = QEs({
                    "match": {
                        "_id": entry.doi
                    }
                })
            elif entry.title:
                query = QEs({
                    "match_phrase": {
                        "title": entry.title
                    }
                })

            search = search.source(excludes=['*'])
            results = search.query(query).execute()

            if results:
                dois_for_entry += [(result.meta.id, entry) for result in results]
                entry.result_found = True
            elif entry.title:

                # If not found try to find the entry by its title using match.
                results = PaperDocument.search().query(QEs({
                    'match': {
                        'title': {
                            'query': entry.title,
                            'minimum_should_match': "90%"
                        }
                    }
                })).execute()

                if results:
                    dois_for_entry.append((results[0].meta.id, entry))
                    entry.result_found = True
                    entry.inexact_result_found = True

        whens = []
        for doi, entry in dois_for_entry:

            if entry.inexact_result_found:
                whens.append(When(pk=doi, then=Value(entry.title)))

        return Paper.objects.filter(pk__in=[doi for doi, _ in dois_for_entry]).annotate(
            entry_title=Case(*whens, default=None, output_field=TextField()))

    @property
    def papers(self):
        raise NotImplementedError()

    @property
    def missing_entries(self):
        raise NotImplementedError()

    @property
    def ignored_raw_entries(self):
        raise NotImplementedError()


class BibFileAnalyzer(LiteratureFileAnalyzer):
    """
    Implements a bib file analyzer.
    """
    def __init__(self, file):

        def customizations(record):
            """Use some functions delivered by the library

            :param record: a record
            :returns: -- customized record
            """
            record = add_plaintext_fields(record)  # Removes {} etc. from a entry and puts them into plain_[entry]
            return record

        parser = BibTexParser()
        parser.customization = customizations
        bib_database = bibtexparser.loads(file, parser)

        file_papers = []
        self._ignored_raw_entries = list()
        self._missing_entries = list()

        for entry in bib_database.entries:
            if "doi" in entry:
                if "title" in entry:
                    file_papers.append(LiteratureEntry(doi=entry["doi"], title=entry["plain_title"]))
                else:
                    file_papers.append(LiteratureEntry(doi=entry["doi"], title=""))
            elif "title" in entry:
                file_papers.append(LiteratureEntry(doi="", title=entry["plain_title"]))
            else:
                self._ignored_raw_entries.append(entry)

        self._papers = self.load_entries_from_database(file_papers)

        for entry in file_papers:
            if not entry.result_found:
                self._missing_entries.append(entry)

    @property
    def papers(self):
        return self._papers

    @property
    def missing_entries(self):
        return self._missing_entries

    @property
    def ignored_raw_entries(self):
        return self._ignored_raw_entries
