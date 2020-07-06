import pickle
from dataclasses import dataclass
import hashlib
from typing import List, Optional, Tuple


@dataclass
class SerializableArticleRecord:
    doi: Optional[str]
    title: Optional[str]
    abstract: Optional[str]
    authors: List[Tuple[str, str]]
    datasource: Optional[str]
    paperhost: Optional[str]
    paperhost_url: Optional[str]
    pubmed_id: Optional[str]
    publication_date: Optional[str]
    url: Optional[str]
    pdf_url: Optional[str]
    version: Optional[str]
    is_preprint: Optional[bool]
    journal: Optional[str]
    update_timestamp: Optional[str]
    _md5: Optional[str] = None

    def __post_init__(self):
        self.authors = sorted(self.authors)

    @property
    def md5(self):
        if not self._md5:
            m = hashlib.md5(pickle.dumps(self))
            self._md5 = m.hexdigest()[:22] # Maximum length of MD5 is 22 hex digits
        return self._md5