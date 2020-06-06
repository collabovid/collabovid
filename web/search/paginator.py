from data.models import Paper
from django.core.paginator import Paginator


class ScoreSortPaginator(Paginator):
    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        paper_score_table = dict()
        for paper_doi, score in self.object_list[bottom:top]:
            paper_score_table[paper_doi] = score
        papers = Paper.objects.filter(pk__in=paper_score_table.keys()).order_by("-published_at")
        papers = sorted(papers, key=lambda paper: paper_score_table[paper.doi], reverse=True)

        return self._get_page(papers, number, self)





