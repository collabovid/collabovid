from data.documents import PaperDocument
from src.search.search import Search, PaperResult

from elasticsearch_dsl import Q as QEs

from typing import List
import time
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
                    'had', 'just', 'over', 'into', 'whats'
                    'next', 'used', 'go' 'know', 'covid19', 'sars' 'mers' 'cov', 'covid-19', 'sars-cov-2']

    @staticmethod
    def remove_common_words(query):
        query = [word for word in query.split() if
                 re.sub(r'[^\x00-\x7F]+', '', word.lower()) not in ElasticsearchQueryHelper.COMMON_WORDS]
        return " ".join(query)


class Elasticsearch(Search):

    def __init__(self, keyword_search: bool, *args, **kwargs):
        super(Elasticsearch, self).__init__(*args, **kwargs)
        self.keyword_search = keyword_search

    def find(self, paper_score_table: dict, query: str, ids: List[str], score_min):
        search = PaperDocument.search()

        print(ElasticsearchQueryHelper.remove_common_words(query))

        if ids is not None:
            search = search.query('ids', values=ids)

        if self.keyword_search:
            search = search.query(QEs('match_phrase', title=query) |
                                  QEs('match', title={'query': query,
                                                      'fuzziness': 'AUTO',
                                                      'boost': 0.8}) |
                                  QEs('match', authors__full_name={'query': query, 'boost': 0.5}))
        else:
            search = search.query(QEs('match_phrase', title=query) |
                                  QEs('match', title={'query': ElasticsearchQueryHelper.remove_common_words(query),
                                                      'fuzziness': 'AUTO', 'boost': 0.8}))
        search = search.source(excludes=['*'])

        total = search.count()
        search = search[0:total]
        print(total)
        results = search.execute()

        max_score = results.hits.max_score

        for i, paper in enumerate(results):
            score = round(paper.meta.score / max_score, 2)
            if score < score_min:
                # Papers are sorted by score
                print(score, i)
                break
            paper_score_table[paper.meta.id] += score

        return query

    def highlights(self, page: dict, query: str, ids: List[str]):
        search = PaperDocument.search()
        search = search.query('multi_match', query=query, fields=['title', 'abstract', 'authors.full_name'],
                              fuzziness='AUTO').highlight(
            'title', 'abstract', 'authors.full_name', number_of_fragments=0, fragment_size=0)
        search = search.query('ids', values=ids)
        total = search.count()
        search = search[0:total]
        search = search.source(excludes=['*'])
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
