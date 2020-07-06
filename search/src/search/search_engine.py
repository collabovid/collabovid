from collections import defaultdict

from django.db.models import Q, F, QuerySet
from django.conf import settings
from data.models import Paper, Author, Journal, Category, CategoryMembership, GeoCity, GeoCountry

from src.search.elasticsearch import ElasticsearchRequestHelper
from src.search.utils import TimerUtilities
from .semantic_search import SemanticSearch
from .development.title_search import TitleSearch

class SearchEngine:
    COMBINED_SEARCH = 1
    KEYWORD_SEARCH = 2

    ARTICLE_TYPE_ALL = 3
    ARTICLE_TYPE_PREPRINTS = 2
    ARTICLE_TYPE_PEER_REVIEWED = 1

    def __init__(self, form):

        if form['tab'] == 'combined':
            self.search_type = SearchEngine.COMBINED_SEARCH
        elif form['tab'] == 'keyword':
            self.search_type = SearchEngine.KEYWORD_SEARCH
        else:
            raise ValueError("No valid tab provided")

        self.form = form

    def filter_papers(self):
        category_ids = self.form['categories']
        start_date = self.form['published_at_start']
        end_date = self.form['published_at_end']

        author_ids = self.form["authors"]
        author_and = (self.form["authors_connection"] == 'all')

        journal_ids = self.form["journals"]
        location_ids = self.form["locations"]

        article_type_string = self.form["article_type"]

        article_type = SearchEngine.ARTICLE_TYPE_ALL

        if article_type_string == 'reviewed':
            article_type = SearchEngine.ARTICLE_TYPE_PEER_REVIEWED
        elif article_type_string == 'preprints':
            article_type = SearchEngine.ARTICLE_TYPE_PREPRINTS

        papers = Paper.objects.all()

        filtered = False

        if article_type != SearchEngine.ARTICLE_TYPE_ALL:
            papers = papers.filter(is_preprint=(article_type == SearchEngine.ARTICLE_TYPE_PREPRINTS))
            filtered = True

        if category_ids and len(category_ids) > 0:
            papers = papers.filter(categories__pk__in=category_ids)
            filtered = True

        if location_ids and len(location_ids) > 0:
            countries = GeoCountry.objects.filter(pk__in=location_ids)
            cities = GeoCity.objects.filter(Q(pk__in=location_ids) | Q(country__in=countries))
            papers = papers.filter(Q(locations__in=cities) | Q(locations__in=countries))
            filtered = True

        if journal_ids and len(journal_ids) > 0:
            journals = Journal.objects.filter(pk__in=journal_ids)
            papers = papers.filter(journal__in=journals)
            filtered = True

        if author_ids and len(author_ids) > 0:
            authors = Author.objects.filter(pk__in=author_ids)

            if author_and:
                for author in authors:
                    papers = papers.filter(authors=author)
            else:
                papers = papers.filter(authors__in=authors)

            filtered = True

        if start_date:
            papers = papers.filter(published_at__gte=start_date)
            filtered = True

        if end_date:
            papers = papers.filter(published_at__lte=end_date)
            filtered = True

        return filtered, papers.distinct()

    def get_papers_no_query(self, papers: QuerySet):
        """
        If the user did not provide a query we want to either show the newest papers or
        show those papers first that have the best matching category. We sort by newest when two papers
        have the same score. Therefore, we either give all papers score 1 or add Category Score.
        """

        category_ids = self.form['categories']

        filtered_dois = list(papers.values_list('doi', flat=True))

        score_table = dict()

        for doi in filtered_dois:
            score_table[doi] = 1

        if category_ids and len(category_ids) == 1:
            try:
                category = Category.objects.get(pk=category_ids[0])

                memberships = CategoryMembership.objects.filter(paper__in=papers, category=category). \
                    annotate(doi=F('paper__doi'))

                for membership in memberships:
                    score_table[membership.doi] = membership.score

            except Category.DoesNotExist:
                raise Exception("Provided unknown category")
            except CategoryMembership.DoesNotExist:
                raise Exception("Filtering yielded incorrect papers for category")

        return score_table

    def search(self):

        query = self.form["query"].strip()

        filtered, papers = self.filter_papers()
        paper_score_table = defaultdict(int)

        if query:
            filtered_dois = None

            if filtered:
                filtered_dois = list(papers.values_list('doi', flat=True))

            if self.search_type == SearchEngine.KEYWORD_SEARCH:
                if settings.USING_ELASTICSEARCH:
                    TimerUtilities.time_function(ElasticsearchRequestHelper.find, paper_score_table, query, ids=filtered_dois)
                else:
                    TimerUtilities.time_function(TitleSearch.find, paper_score_table, query, papers=papers)
            elif self.search_type == SearchEngine.COMBINED_SEARCH:
                TimerUtilities.time_function(SemanticSearch.find, paper_score_table, query, ids=filtered_dois)

                if settings.USING_ELASTICSEARCH:
                    TimerUtilities.time_function(ElasticsearchRequestHelper.enhance_results, paper_score_table, query,
                                                 influence=0.6)
            else:
                raise ValueError("No valid search type provided")
        else:
            return self.get_papers_no_query(papers)

        return paper_score_table
