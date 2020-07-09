import json
from dataclasses import dataclass, field
import hashlib
from datetime import date
from typing import List, Optional, Tuple

from django.core.serializers.json import DjangoJSONEncoder


@dataclass
class SerializableArticleRecord:
    doi: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[Tuple[str, str]] = field(default_factory=list)
    datasource: Optional[str] = None
    paperhost: Optional[str] = None
    paperhost_url: Optional[str] = None
    pubmed_id: Optional[str] = None
    publication_date: Optional[date] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    version: Optional[str] = None
    is_preprint: Optional[bool] = None
    journal: Optional[str] = None
    update_timestamp: Optional[str] = None
    _md5: Optional[str] = None

    @property
    def md5(self):
        if not self._md5:
            m = hashlib.md5(self.json().encode('utf-8'))
            self._md5 = m.hexdigest()[:22]  # Maximum length of MD5 is 22 hex digits
        return self._md5

    def json(self):
        self.authors = sorted(self.authors)
        return json.dumps(self.__dict__, sort_keys=True, cls=DjangoJSONEncoder)
