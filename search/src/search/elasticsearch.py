from data.documents import PaperDocument, AuthorDocument

from elasticsearch_dsl import Q as QEs

from typing import List
import re


class ElasticsearchQueryHelper:
    COMMON_WORDS = ['the', 'of', 'and', 'to', 'a', 'in', 'for', 'is', 'on', 'that', 'by', 'this', 'with', 'i', 'you',
                    'it', 'not', 'or', 'be', 'are', 'from', 'at', 'as', 'your', 'all', 'have', 'new', 'more', 'an',
                    'was', 'we', 'will', 'can', 'us', 'about', 'if', 'my', 'has',
                    'but', 'our', 'one', 'other', 'do', 'no', 'time', 'they', 'site', 'he', 'up', 'may',
                    'what', 'which', 'their', 'out', 'use', 'any', 'there', 'see', 'only', 'so', 'his', 'when',
                    'here', 'who', 'web', 'also', 'now', 'help', 'get',
                    'first', 'am', 'been', 'would', 'how', 'were', 'me', 'some', 'these',
                    'its', 'like', 'than', 'find',
                    'had', 'just', 'over', 'into', 'whats',
                    'next', 'used', 'go' 'know', 'know', 'covid19', 'sars' 'mers' 'cov',
                    'covid-19', 'sars-cov-2']

    @staticmethod
    def remove_common_words(query):
        query = [word for word in query.split() if
                 re.sub(r'[^\x00-\x7F]+', '', word.lower()) not in ElasticsearchQueryHelper.COMMON_WORDS]
        return " ".join(query)


class ElasticsearchRequestHelper:

    @staticmethod
    def _get_title_exact_match(query: str, boost=1):
        return QEs({
            'match_phrase': {
                'title': {
                    'query': query
                }
            }
        })

    @staticmethod
    def _get_title_match(query: str, boost=0.8):
        return QEs('match', title={'query': query,
                                   'fuzziness': 'AUTO',
                                   'boost': boost})

    @staticmethod
    def _get_abstract_match(query: str, boost=0.8):
        return QEs('match', abstract={'query': query,
                                      'fuzziness': 'AUTO',
                                      'boost': boost})

    @staticmethod
    def _get_author_match(query: str, boost=0.8):
        return QEs('match', authors__full_name={'query': query,
                                                'boost': boost})

    @staticmethod
    def _get_ids_match(ids: List[str]):
        return QEs('ids', values=ids)

    @staticmethod
    def _build_search_request(must_match, should_match):

        search = PaperDocument.search()
        search = search.query(QEs('bool',
                                  must=must_match,
                                  should=should_match,
                                  minimum_should_match=1))

        return search.source(excludes=['*'])

    @staticmethod
    def enhance_results(score_table: dict, query: str, influence: float = 0.5):
        """
        Used for enhancing existing search results, i.e. potentially reordering them.
        :param score_table:
        :param query:
        :param influence
        :return:
        """

        should_match = []
        must_match = []

        must_match.append(ElasticsearchRequestHelper._get_ids_match(list(score_table.keys())))
        should_match.append(ElasticsearchRequestHelper._get_title_exact_match(query) |
                            ElasticsearchRequestHelper._get_title_match(
                                query=ElasticsearchQueryHelper.remove_common_words(query)
                            ))

        search = ElasticsearchRequestHelper._build_search_request(must_match, should_match)

        total = search.count()
        search = search[0:total]
        results = search.execute()

        max_score = results.hits.max_score

        for i, paper in enumerate(results):
            score = round(paper.meta.score / max_score, 2)
            score_table[paper.meta.id] += score

    @staticmethod
    def find(score_table: dict, query: str, ids: List[str]):

        should_match = []
        must_match = []

        if ids:
            must_match.append(ElasticsearchRequestHelper._get_ids_match(ids))

        should_match.append(ElasticsearchRequestHelper._get_title_exact_match(query) |
                            ElasticsearchRequestHelper._get_title_match(query) |
                            ElasticsearchRequestHelper._get_author_match(
                                ElasticsearchQueryHelper.remove_common_words(query))
                            )

        search = ElasticsearchRequestHelper._build_search_request(must_match, should_match)
        total = search.count()
        search = search[0:total]
        results = search.execute()

        for i, paper in enumerate(results):
            score_table[paper.meta.id] = paper.meta.score

        return query

    @staticmethod
    def authors(authors: List, query: str, excluded_author_ids: List, max_author_count: int = 8):
        search = AuthorDocument.search()
        search = search.query(QEs('bool',
                                  should=[QEs('match', full_name={
                                      'query': ElasticsearchQueryHelper.remove_common_words(query)})],
                                  must_not=[QEs('ids', values=excluded_author_ids)])) \
            .highlight('full_name', number_of_fragments=0, fragment_size=0)

        search = search[0:max_author_count]
        results = search.execute()

        for result in results:
            if hasattr(result.meta, 'highlight'):
                if hasattr(result.meta.highlight, 'full_name'):
                    authors.append({'pk': result.meta.id, 'full_name': result.meta.highlight.full_name[0]})

    @staticmethod
    def highlights(page: dict, query: str, ids: List[str]):

        should_match = []
        must_match = []

        if ids:
            must_match.append(ElasticsearchRequestHelper._get_ids_match(ids))

        should_match.append(ElasticsearchRequestHelper._get_title_exact_match(query) |
                            ElasticsearchRequestHelper._get_abstract_match(query) |
                            ElasticsearchRequestHelper._get_title_match(query) |
                            ElasticsearchRequestHelper._get_author_match(
                                ElasticsearchQueryHelper.remove_common_words(query)
                            ))

        search = ElasticsearchRequestHelper._build_search_request(must_match, should_match).highlight(
            'title', 'abstract', 'authors.full_name', number_of_fragments=0, fragment_size=0)

        total = search.count()
        search = search[0:total]

        results = search.execute()

        for result in results:
            if hasattr(result.meta, 'highlight'):
                if hasattr(result.meta.highlight, 'title'):
                    page[result.meta.id]['title'] = "".join(result.meta.highlight.title[0])
                if hasattr(result.meta.highlight, 'abstract'):
                    page[result.meta.id]['abstract'] = result.meta.highlight.abstract[0]
                if hasattr(result.meta.highlight, 'authors.full_name'):
                    page[result.meta.id]['authors.full_name'] = [str(name) for name in
                                                                 result.meta.highlight['authors.full_name']]
