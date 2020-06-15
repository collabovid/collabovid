import re

import spacy

from src.geo.geoname_db import GeonamesDB


_SPACY_MODEL = 'en_core_web_lg'

_COUNTRY_ALIASES = {
    "US": "United States",
    "U.S.A": "United States",
    "U.S": "United States",
}

class GeoParser:
    def __init__(self, db_path):
        self.nlp = spacy.load(_SPACY_MODEL)
        self.geonames_db = GeonamesDB(db_path)
        self.geonames_db.connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.geonames_db.close_session()

    def parse(self, query, merge=False):
        doc = self.nlp(query)
        locations = []
        ignored_entities = []
        for entity in doc.ents:
            if entity.label_ == 'GPE':
                term = self._resolve_alias(entity.text)
                location = self._get_geonames_location(term)

                if location:
                    usage = {
                        'word': entity.text,
                        'start': entity.start_char,
                        'end': entity.end_char,
                    }
                    locations.append((location, usage))
                else:
                    ignored_entities.append(entity.text)

        if merge:
            return self._merge_locations(query, locations), ignored_entities
        return locations, ignored_entities

    def _get_geonames_location(self, term):
        try:
            return self.geonames_db.search_most_probable(term)
        except GeonamesDB.RecordNotFound:
            pass

        alt_term = self._get_alternate_term(term)
        if term != alt_term:
            try:
                return self.geonames_db.search_most_probable(alt_term)
            except GeonamesDB.RecordNotFound:
                pass
        return None

    @staticmethod
    def _merge_locations(query, locations):
        """
        Merge locations, following the pattern r"_Location_(( Province| City)?, ?)(_Country_)$"
        Examples:
            Braunschweig, Germany
            Wuhan Province, China
            Los Angeles City, USA
        """
        location_suffix_pattern = r'(( Province| City)?, ?)(.*)$'

        merged_locations = []
        for location, usage in locations:
            match = re.match(location_suffix_pattern, query[usage['end']:])
            if match:
                idx = usage['end'] + len(match.group(1))
                try:
                    suc_location, suc_usage = next((loc, use) for loc, use in locations if use['start'] == idx)
                except StopIteration:
                    continue

                if (suc_location.country_code == location.country_code and
                        (suc_location.feature_label == "A.PCLI" or
                            (suc_location.feature_label == "A.ADM1" and
                                suc_location.admin1_code == location.admin1_code))):
                    span_end = suc_usage['end']
                    usage['word'] = query[usage['start']:span_end]
                    usage['end'] = span_end
                    merged_locations.append((suc_location, suc_usage))

        return [x for x in locations if x not in merged_locations]

    @staticmethod
    def _resolve_alias(text):
        if text in _COUNTRY_ALIASES:
            return _COUNTRY_ALIASES[text]
        else:
            return text

    @staticmethod
    def _get_alternate_term(text):
        ltext = text.lower()

        prefixes = ['the ']
        suffices = [' province', ' city', ' district', ' state', ' region']

        for prefix in prefixes:
            if ltext.startswith(prefix):
                return text[len(prefix):]

        for suffix in suffices:
            if ltext.endswith(suffix):
                return text[:-len(suffix)]

        return text
