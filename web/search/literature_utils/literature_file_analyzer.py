import rispy

from data.models import Paper


class LiteratureEntry:

    def __init__(self, doi, title):
        self._doi = doi
        self._title = title

    @property
    def title(self):
        return self._title

    @property
    def doi(self):
        return self._doi


class LiteratureFileAnalyzer:

    @property
    def papers(self):
        raise NotImplementedError()

    @property
    def missing_entries(self):
        raise NotImplementedError()

    @property
    def ignored_raw_entries(self):
        raise NotImplementedError()


class RisFileAnalyzer(LiteratureFileAnalyzer):

    def __init__(self, file):
        entries = rispy.loads(file)

        file_papers = []
        self._ignored_raw_entries = list()
        self._missing_entries = list()

        for entry in entries:
            if "doi" in entry and "primary_title" in entry:
                file_papers.append(LiteratureEntry(doi=entry["doi"], title=entry["primary_title"]))
            else:
                self._ignored_raw_entries.append(entry)

        self._papers = Paper.objects.filter(pk__in=[entry.doi for entry in file_papers])

        paper_dois = set(self._papers.values_list('doi', flat=True))

        for paper in file_papers:
            if paper.doi not in paper_dois:
                self._missing_entries.append(paper)

    @property
    def papers(self):
        return self._papers

    @property
    def missing_entries(self):
        return self._missing_entries

    @property
    def ignored_raw_entries(self):
        return self._ignored_raw_entries

