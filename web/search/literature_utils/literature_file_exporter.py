import rispy
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import io
from django.db.models import QuerySet
from django.http import HttpResponse


class LiteratureFileExporter:
    CONTENT_TYPE = None
    EXTENSION = None

    def __init__(self, papers: QuerySet):
        self._papers = papers

    def export(self):
        raise NotImplementedError()

    def build_response(self):
        file = self.export()

        response = HttpResponse(file.getvalue(), content_type=self.CONTENT_TYPE)
        response['Content-Disposition'] = 'attachment; filename=' + self.filename()

        return response

    @classmethod
    def filename(cls):
        return "collabovid-export" + cls.EXTENSION


class RisFileExporter(LiteratureFileExporter):
    CONTENT_TYPE = "application/x-research-info-systems"
    EXTENSION = ".ris"

    def export(self):

        # Open StringIO to grab in-memory file contents
        file = io.StringIO()

        entries = list()

        for paper in self._papers:
            entry = {
                'primary_title': paper.title,
                'first_authors': [", ".join([author.last_name, author.first_name]) for author in
                                  paper.authors.all()],
                'abstract': paper.abstract,
                'doi': paper.doi,
                'publication_year': paper.published_at.year,
                'publisher': paper.host.name
            }

            if paper.pdf_url:
                entry['url'] = paper.pdf_url

            if paper.journal:
                entry['journal_name'] = paper.journal.displayname
                entry['type_of_reference'] = 'JOUR'
            else:
                entry['type_of_reference'] = 'GEN'

            entries.append(entry)

        rispy.dump(entries, file)

        return file


class BibTeXFileExporter(LiteratureFileExporter):
    CONTENT_TYPE = 'application/x-bibtex'
    EXTENSION = '.bib'

    def generate_id(self, paper):
        id_filer = filter(str.isalnum, paper.authors.first().last_name.split()[0] +
                          paper.title.split()[0] + str(paper.published_at.year))

        return "".join(id_filer)

    def generate_authors(self, paper):
        return " and ".join(["{" + ", ".join([author.last_name, author.first_name]) + "}" for author in
                             paper.authors.all()])

    def export(self):
        # Open StringIO to grab in-memory file contents
        file = io.StringIO()

        db = BibDatabase()

        for paper in self._papers:
            entry = {
                'abstract': paper.abstract,
                'title': paper.title,
                'year': str(paper.published_at.year),
                'ID': self.generate_id(paper),
                'doi': paper.doi,
                'author': self.generate_authors(paper)
            }

            if paper.journal:
                entry['journal'] = paper.journal.displayname

            if paper.is_preprint:
                entry['ENTRYTYPE'] = 'unpublished'
            else:
                entry['ENTRYTYPE'] = 'article'

            db.entries.append(entry)

        writer = BibTexWriter()
        file.write(writer.write(db))
        return file
