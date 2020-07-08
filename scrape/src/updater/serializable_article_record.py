import json
from dataclasses import dataclass, field
import hashlib
from datetime import date
from typing import List, Optional, Tuple

from django.core.serializers.json import DjangoJSONEncoder

from data.models import DataSource


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
        data_dict = self.__dict__
        data_dict.pop('_md5', None)
        return json.dumps(data_dict, sort_keys=True, cls=DjangoJSONEncoder)

    @staticmethod
    def from_article(db_article):
        authors = sorted([(a.last_name, a.first_name) for a in db_article.authors.all()])
        journal = db_article.journal.name if db_article.journal else None
        return SerializableArticleRecord(doi=db_article.doi, title=db_article.title, abstract=db_article.abstract, authors=authors,
                                paperhost=db_article.host.name, paperhost_url=db_article.host.url, journal=journal,
                                datasource=DataSource(db_article.data_source_value), pubmed_id=db_article.pubmed_id,
                                publication_date=db_article.published_at, url=db_article.url, pdf_url=db_article.pdf_url,
                                version=db_article.version, is_preprint=db_article.is_preprint)