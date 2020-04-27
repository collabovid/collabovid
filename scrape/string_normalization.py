import re
from typing import List

_HORIZONTAL_SPACE_PATTERN = r'[ \t]'
_PUNCTATION_CHARS_PATTERN = r'[.,;:(){}&/]'
_PARANTHESES_PATTERN = r'[\[\](){}]'
_QUOTES_PATTERN = r'[\'"”“]'
_DOI_PATTERN = r'(doi:)?10\.\d+/\S+'
_HTTPS_PREFIX_PATTERN = r'https?://(www.)?'
_URL_PATTERN = rf'({_HTTPS_PREFIX_PATTERN}\S+|\S+.(com|org|gov)(/\S+)?)'
_DOI_URL_PATTERN = rf'({_HTTPS_PREFIX_PATTERN})?doi\.org/{_DOI_PATTERN}'
_CC_LICENSE_PATTERN = r'CC-BY(-NC)?(-ND)? 4\.0 International license'
_CC_LICENSE_URL_PATTERN = rf'{_HTTPS_PREFIX_PATTERN}creativecommons.org/licenses/by(-nc)?(-nd)?/4.0/?'


def remove_from_list(list: List[str], *patterns: str):
    combined_regex = re.compile("(" + ")|(".join(patterns) + ")")
    return [el for el in list if not combined_regex.fullmatch(el)]


def _remove(pattern: str, text: str, force_spaces: bool = False):
    if force_spaces:
        substituted = re.sub(rf'(^|\n){_HORIZONTAL_SPACE_PATTERN}*{pattern}{_HORIZONTAL_SPACE_PATTERN}*($|\n)', '\n',
                             text)
        substituted = re.sub(rf'(^|\n){_HORIZONTAL_SPACE_PATTERN}*{pattern}{_HORIZONTAL_SPACE_PATTERN}+', '\n', substituted)
        substituted = re.sub(rf'{_HORIZONTAL_SPACE_PATTERN}+{pattern}{_HORIZONTAL_SPACE_PATTERN}*($|\n)', '\n', substituted)
        substituted = re.sub(rf'{_HORIZONTAL_SPACE_PATTERN}+{pattern}{_HORIZONTAL_SPACE_PATTERN}+', ' ', substituted)
    else:
        substituted = re.sub(rf'(^|\n){_HORIZONTAL_SPACE_PATTERN}*{pattern}{_HORIZONTAL_SPACE_PATTERN}*($|\n)', '\n', text)
        substituted = re.sub(rf'{_HORIZONTAL_SPACE_PATTERN}*{pattern}{_HORIZONTAL_SPACE_PATTERN}*', ' ', substituted)
    return substituted


def remove_punctation(text: str):
    return _remove(_PUNCTATION_CHARS_PATTERN, text)


def remove_parantheses(text: str):
    return _remove(_PARANTHESES_PATTERN, text)


def remove_quotes(text: str):
    return _remove(_QUOTES_PATTERN, text)


def remove_urls(text: str):
    return _remove(_URL_PATTERN, text)


def remove_doi(text: str):
    return _remove(_DOI_PATTERN, text)


def remove_separated_numbers(text: str):
    return _remove(r'([-.,]|\d)+', text, force_spaces=True)


def remove(text: str, punctation: bool = False, parantheses: bool = False, quotes: bool = False, urls: bool = False,
           doi: bool = False, numbers: bool = False):
    substituted_text = text
    if urls:
        substituted_text = remove_urls(substituted_text)
    if doi:
        substituted_text = remove_doi(substituted_text)
    if punctation:
        substituted_text = remove_punctation(substituted_text)
    if parantheses:
        substituted_text = remove_parantheses(substituted_text)
    if quotes:
        substituted_text = remove_quotes(substituted_text)
    if numbers:
        substituted_text = remove_separated_numbers(substituted_text)
    return substituted_text


def remove_medrxiv_header(text: str):
    return re.sub(
        r'(('
        r'is the|'
        r'\(which was not peer-reviewed\)|'
        r'The copyright holder for this preprint|'
        r'It is made available under a|'
        r'author/funder, who has granted medRxiv a license to display the preprint in perpetuity\.|'
        rf'\.? ?{_CC_LICENSE_PATTERN}|'
        rf'{_DOI_URL_PATTERN}: medRxiv preprint|'
        rf'{_CC_LICENSE_URL_PATTERN}'
        r')\s*)+',
        '',
        text
    )


def remove_biorxiv_header(text: str):
    return re.sub(
        r'(('
        r'was not certified by peer review\)|'
        r'\(which|'
        r'is the author/funder\.|'
        r'It is made available under a|'
        r'this version posted \S+ \d+, \d+\.|'
        rf'\.? ?{_CC_LICENSE_PATTERN}|'
        rf'{_DOI_URL_PATTERN}: bioRxiv preprint|'
        rf'{_CC_LICENSE_URL_PATTERN}'
        r')\s*)+',
        '',
        text
    )


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


def normalize_pdf_content(text: str):
    return remove_medrxiv_header(remove_biorxiv_header(text))