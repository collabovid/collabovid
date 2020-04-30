import re

_DOI_PATTERN = r'10.\d{4,9}/\S+'


def is_doi(text: str):
    return re.fullmatch(_DOI_PATTERN, text)