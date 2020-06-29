from data.models import Paper
from django.core.paginator import Paginator


class FakePaginator(Paginator):
    def __init__(self, total_count, per_page, papers, page):
        super(FakePaginator, self).__init__(range(total_count), per_page)
        self.papers = papers
        self.fixed_page = page

    def page(self, number):
        return self._get_page(self.papers, self.fixed_page, self)





