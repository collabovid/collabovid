from data.documents import PaperDocument
from src.search.search import Search, PaperResult

from typing import List
import time


class Elasticsearch(Search):

    def find(self, paper_score_table: dict, query: str, ids: List[str], score_min):
        search = PaperDocument.search()

        search = search.query('ids', values=ids)
        search = search.query('match', title={'query': query, 'fuzziness': 'AUTO', 'minimum_should_match': '80%'})
        search = search.source(excludes=['*'])

        total = search.count()
        search = search[0:total]
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
        search = search.query('multi_match', query=query, fields=['title', 'abstract'], fuzziness='AUTO').highlight('title', 'abstract', number_of_fragments=0, fragment_size=0)
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

