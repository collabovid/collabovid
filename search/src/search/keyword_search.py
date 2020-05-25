import os
import re
from collections import defaultdict

import nltk
from django.db.models import Q, QuerySet

from .search import Search, PaperResult
from typing import List
from data.models import Paper

AUTHOR_ADDITIVE_SCORE = 2  # Score per matching author
TITLE_ADDITIVE_SCORE = 0.4  # Score per matching keyword in title
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

        query = Q()
        for word in keywords:
            query |= Q(title__icontains=word)
            query |= Q(abstract__icontains=word)

        filtered_papers = filtered_papers.filter(query)

        filtered_papers = filtered_papers.distinct()

        paper_dois = filtered_papers.values_list('doi', flat=True)

        # Compute the individual paper scores based on the matches
        summed_scores = defaultdict(float)
        for paper in filtered_papers:

            if paper.title == query:
                summed_scores[paper.doi] += 2

            for word in keywords:
                # We only count the first type of match (which gives the most points). So we do not count any word twice
                if re.search(word, paper.title, re.IGNORECASE):
                    summed_scores[paper.doi] += TITLE_ADDITIVE_SCORE
                elif re.search(word, paper.abstract, re.IGNORECASE):
                    summed_scores[paper.doi] += ABSTRACT_ADDITIVE_SCORE

        if len(summed_scores) > 0:
            max_score = max(max(summed_scores.values()), 1)
        else:
            max_score = 1

        return [PaperResult(paper_doi=doi,
                            score=summed_scores[doi] / max_score)
                for doi in paper_dois]
