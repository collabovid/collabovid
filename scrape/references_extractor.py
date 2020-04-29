import random
import re
from collections import defaultdict
from time import sleep

import pymed
import requests
import scholarly
from bs4 import BeautifulSoup
from scholarly import Publication
from tika import parser
from nltk import ngrams

import scrape.string_normalization as stromalization

_PUBMED_URL = 'https://www.ncbi.nlm.nih.gov/pubmed/{0}'
_PUBMED = pymed.PubMed('corona-tracker', 'testmail')


def _pubmed_query(query: str):
    sleep(1)
    return list(_PUBMED.query(query))


def _to_dict(pubmed_obj):
    data = {}

    data['url'] = _PUBMED_URL.format(pubmed_obj.pubmed_id.split()[0])
    data['title'] = pubmed_obj.title
    data['journal'] = pubmed_obj.journal
    authors = ', '.join([f"{author['firstname']} {author['lastname']}" for author in pubmed_obj.authors])
    if len(authors) > 200:
        authors = f"{authors[:197]}..."
    data['authors'] = authors
    data['publication_date'] = str(pubmed_obj.publication_date)

    return data


def get_pubmed_url(word_list: str):
    if len(word_list) == 0:
        return None

    response = _pubmed_query(' '.join(word_list))
    if len(response) == 1:
        print("Found result")

        return _to_dict(response[0])
    elif len(response) > 1:
        print(f"Found {len(response)} results")
        return None
    else:
        tengrams = list(ngrams(word_list, 10))
        print(f"Test {len(tengrams)} 10-grams")
        count = 1
        for tengram in tengrams:
            print(f"Try {count}. tengram")
            sleep(3)
            response = _pubmed_query(' '.join(tengram))
            if len(response) == 1:
                print("Found URL")
                return _to_dict(response[0])
            elif len(response) > 1:
                print(f"Found {len(response)} results")
            else:
                print(f"Found no result")
            count += 1
        return None


def extract_references(path: str):
    parsed_data = parser.from_file(path)

    if 'content' in parsed_data:
        text = parsed_data['content']
    else:
        raise

    text = stromalization.remove_medrxiv_header(stromalization.remove_biorxiv_header(text))
    lines = [line.strip() for line in text.split('\n') if line.strip() != '']
    lines = stromalization.remove_linenumbers(lines)

    reference_keyword_idx = [idx for idx, line in enumerate(lines) if re.match(r'^references:?( \d+)?$', line.lower())]

    if len(reference_keyword_idx) == 0:
        return []
    elif len(reference_keyword_idx) > 1:
        print(text)
    else:
        reference_keyword_idx = reference_keyword_idx[0]

    document_rest = lines[reference_keyword_idx + 1:]

    reference_start_patterns = [
        r'^\d{1,3}\. ',
        r'^\[\d{1,3}\] ',
        r'\[[a-zA-Z]+\] ',
    ]

    pattern_score = []

    for pattern in reference_start_patterns:
         pattern_score.append(len([line for line in document_rest if re.match(pattern, line)]))

    max_score = sorted([(idx, score) for idx, score in enumerate(pattern_score)], key=lambda x:x[1])[-1]
    print(f"Selected Pattern: {reference_start_patterns[max_score[0]]} with {max_score[1]} occurences")

    if max_score[1] == 0:
        return []

    references = []
    current = None
    for line in document_rest:
        match = re.match(reference_start_patterns[max_score[0]], line)
        if match:
            if current:
                references.append(current.replace('\n', ' '))
            current = line[len(match.group(0)):]
        else:
            if current:
                current += '\n' + line

    if current:
        attachment_keywords = r'^([Ff]igures?|(Tt]ables?|[Aa]ttachments?)|[Aa]bbreviations|[Aa]cknowledge|[Cc]onflicts of interest)'
        pattern = re.compile(attachment_keywords, re.MULTILINE)
        attachment_keyword_matches = pattern.finditer(current)
        #attachment_keyword_matches = re.finditer(r'^([Ff]igures?|(Tt]ables?|[Aa]ttachments?)|[Aa]bbreviations|[Aa]cknowledge|[Cc]onflicts of interest)', current)
        try:
            first_match = next(attachment_keyword_matches)
            first_match_start_idx = first_match.start()
            references.append(current[:first_match_start_idx])
        except:
            references.append(current)

    for idx, ref in enumerate(references):
        print(f"{idx}: {ref}")

    # refs_with_url = []
    normalized_refs = []
    for idx, ref in enumerate(references):
         normalized_ref = stromalization.remove(
             ref,
             'et al',
             'vol',
             'pp',
             '\S{1,2}',
             '([- .,]|\d)+',
             punctation=True,
             parantheses=True,
             quotes=True,
             urls=True,
             doi=True,
             numbers=True,
             breaks=True
         )

         print(f"{idx}: {normalized_ref}")

         word_list = normalized_ref.split()
         word_list = stromalization.remove_from_list(
             word_list,
             'et al',
             'vol',
             'pp',
             r'\S{1,2}',
             r'([- .,]|\d)+',
         )

         if any(x in normalized_ref for x in ('arxiv', 'medrxiv', 'biorxiv')):
             result = None
         else:
             result = get_pubmed_url(word_list)
         normalized_refs.append((ref, result, normalized_ref))

    return normalized_refs