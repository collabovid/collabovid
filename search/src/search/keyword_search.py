import os
import re
from collections import defaultdict

import nltk
from django.db.models import Q, QuerySet

from .search import Search, PaperResult
from typing import List
from data.models import Paper

# TODO: Adjust scores after more testing.
AUTHOR_ADDITIVE_SCORE = 0.5  # Score per matching author
TITLE_ADDITIVE_SCORE = 0.2  # Score per matching keyword in title
ABSTRACT_ADDITIVE_SCORE = 0.1  # Score per matching keyword in abstract

# Download nltk stopwords, if not exist
try:
    nltk.data.find('stopwords')
except LookupError:
    if 'NLTK_DATA' in os.environ:
        nltk_data_dir = os.environ['NLTK_DATA']
        nltk.download('stopwords', download_dir=nltk_data_dir)
    else:
        nltk.download('stopwords')
stopwords = set(nltk.corpus.stopwords.words('english'))


class KeywordSearch(Search):
    @staticmethod
    def _get_score(summed_score, word_count):
        """ Returns score in [0,1], depending on the matches of the query. Summed score may be larger, if query is short
        and a large portion of words match an author. """
        return min(1, summed_score / (word_count * TITLE_ADDITIVE_SCORE))

    def find(self, query: str, papers: QuerySet) -> List[PaperResult]:
        """
        Search for records, containing all keywords of query, either in the title, abstract, or an authors last name.
        Stopwords are excluded before. If all words in query are stopwords, use stopwords instead.
        :param query: Search query.
        :return: DOIs of papers, containing the keywords.
        """
        keywords = set(query.split()) - stopwords
        if len(keywords) == 0:
            # In case that query consists of stopwords only, use stopwords for search
            keywords = query.split()

        filtered_papers = Paper.objects.all()
        for word in keywords:
            filtered_papers = filtered_papers.filter(
                (Q(title__icontains=word) | Q(abstract__icontains=word) | Q(authors__last_name__iexact=word)))

        filtered_papers = filtered_papers.distinct()

        paper_dois = filtered_papers.values_list('doi', flat=True)

        # Compute the individual paper scores based on the matches
        summed_scores = defaultdict(int)
        for paper in filtered_papers:
            for word in keywords:
                # We only count the first type of match (which gives the most points). So we do not count any word twice
                author_matched = False
                for author in paper.authors.all():
                    if author.last_name.lower() == word.lower():
                        summed_scores[paper.doi] += AUTHOR_ADDITIVE_SCORE
                        author_matched = True
                        break
                if author_matched:
                    continue
                if re.search(word, paper.title, re.IGNORECASE):
                    summed_scores[paper.doi] += TITLE_ADDITIVE_SCORE
                elif re.search(word, paper.abstract, re.IGNORECASE):
                    summed_scores[paper.doi] += ABSTRACT_ADDITIVE_SCORE
        return [PaperResult(paper_doi=doi,
                            score=KeywordSearch._get_score(summed_scores[doi], len(keywords)))
                for doi in paper_dois]
