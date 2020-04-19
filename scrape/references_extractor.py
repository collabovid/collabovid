import re
import random
from time import sleep
from typing import List

import requests
from bs4 import BeautifulSoup
from scholarly import Publication
from tika import parser
import scholarly


def blubber(soup):
    while True:
        for row in soup.find_all('div', 'gs_or'):
            yield Publication(row, 'scholar')
        else:
            break


def get_paper_url(query: str):
    base_url = 'https://scholar.google.com/scholar?q='
    url = f'{base_url}{query}'

    sleep(random.randrange(0, 5))
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Request error: {response.status_code} ({response.reason})")
        return None

    if 'Bitte zeigen Sie uns, dass Sie kein Roboter sind' in response.text:
        print("Roboter Fick")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    search_result = blubber(soup)

    try:
        first_result = next(search_result)
    except StopIteration:
        print("No search result found on Scholar")
        return None

    try:
        next(search_result)
        print("More than one search result found on Scholar")
        return None
    except StopIteration:
        print("Found paper on Scholar")
        return first_result.bib['url'] if 'url' in first_result.bib else None


def remove_linenumbers(lines: List[str]):
    current_ln = 1

    sanitized_lines = []

    for line in lines:
        if line.endswith(str(current_ln)):
            number_length = len(str(current_ln))
            sanitized_lines.append(line[:-number_length].strip())
            current_ln +=1
        else:
            sanitized_lines.append(line)

    print(f"Removed {current_ln - 1} line numbers")
    return sanitized_lines


def extract_references(path: str):
    parsed_data = parser.from_file(path)

    if 'content' in parsed_data:
        text = parsed_data['content']
    else:
        raise

    text = re.sub(
        ' \. CC-BY(-NC-ND)? 4\.0 International licenseIt is made available under a \n'
        '(is the )?author/funder, who has granted medRxiv a license to display the preprint in perpetuity\. \n'
        '\n'
        '( is the)?\(which was not peer-reviewed\) The copyright holder for this preprint \.\S*: medRxiv preprint \n'
        '\n'
        '\S*\n'
        'http://creativecommons\.org/licenses/by(-nc-nd)?/4\.0/',
        '',
        text
    )

    text = re.sub(
        'All rights reserved\. No reuse allowed without permission\. \n'
        'The copyright holder for this preprint \(which was not peer-reviewed\) is the author/funder\.\. \S*: bioRxiv preprint \n'
        '\n'
        #'[^\n]\n'
        'https://\S+',
        '',
        text
    )

# All rights reserved. No reuse allowed without permission.
    # The copyright holder for this preprint (which was not peer-reviewed) is the author/funder.. https://doi.org/10.1101/782409doi: bioRxiv preprint
    #
    # https://doi.org/10.1101/782409

    lines = [line.strip() for line in text.split('\n') if line.strip() != '']
    lines = remove_linenumbers(lines)

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

    # refs_with_url = []
    # for idx, ref in enumerate(references):
    #     print(f"{idx}: {ref}")
    #     refs_with_url.append((ref, get_paper_url(ref)))

    return [(ref, None) for ref in references]


if __name__ == '__main__':
    search_query = scholarly.search_pubs_query("Zou L, Ruan F, Huang M, et al. SARS-CoV-2 Viral Load in Upper Respiratory Specimens of Infected Patients. New England Journal of Medicine 2020;382:1177-9")
    a = next(search_query)
    pass