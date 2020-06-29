from data.documents import PaperDocument
from src.search.search import Search, PaperResult

from typing import List
import time


class Elasticsearch(Search):

    def find(self, paper_score_table: dict, query: str, ids: List[str], score_min):
        search = PaperDocument.search()

        print("Here1")
        search = search.query('ids', values=ids)
        search = search.query('match', title={'query': query, 'fuzziness': 'AUTO', 'minimum_should_match': '80%'})
        search = search.source(excludes=['*'])

        print("Here2")

        total = search.count()
        print(total)
        search = search[0:total]

        t0 = time.time()
        results = search.execute()

        t1 = time.time()
        print(t1 - t0)

        print("Here3")

        max_score = results.hits.max_score

        for i, paper in enumerate(results):
            score = round(paper.meta.score / max_score, 2)
            if score < score_min:
                # Papers are sorted by score
                print(score, i)
                break
            paper_score_table[paper.meta.id] += score

        print("Here4", flush=True)

        return query

    def highlights(self, query: str, ids: List[str]):
        search = PaperDocument.search()
        search = search.query('multi_match', query=query, fields=['title', 'abstract'], fuzziness='AUTO').highlight('title', 'abstract', number_of_fragments=0, fragment_size=0)
        search = search.query('ids', values=ids)
        total = search.count()
        print("Here4")
        search = search[0:total]
        search = search.source(excludes=['*'])
        results = search.execute()

        highlights = dict()

        for doi in ids:
            highlights[doi] = dict()
            highlights[doi]['doi'] = doi

        for result in results:
            if hasattr(result.meta, 'highlight'):
                if hasattr(result.meta.highlight, 'title'):
                    highlights[result.meta.id]['title'] = "".join(result.meta.highlight.title[0])

                if hasattr(result.meta.highlight, 'abstract'):
                    print(len(result.meta.highlight.abstract))
                    highlights[result.meta.id]['abstract'] = result.meta.highlight.abstract[0]
                    print(result.meta.highlight.abstract)

        print("Here5")

        return [highlights[doi] for doi in ids]
