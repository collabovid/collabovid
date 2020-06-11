import re

import spacy

from src.geo.geoname_db import GeonamesDB

_COUNTRY_ALIASES = {
    "US": "United States",
    "U.S.A": "United States",
}

RED   = "\033[1;31m"
RESET = "\033[0;0m"

class GeoParser:
    def __init__(self, db_path, log=print):
        self.nlp = spacy.load('en_core_web_lg')
        self.log=log
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
                try:
                    location = self.geonames_db.search_most_probable(term)
                except GeonamesDB.RecordNotFound:
                    location = None

                if not location:
                    alt_term = self._get_alternate_term(term)
                    if term != alt_term:
                        try:
                            location = self.geonames_db.search_most_probable(alt_term)
                        except GeonamesDB.RecordNotFound:
                            location = None

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

                if (
                        suc_location.feature_label == "A.PCLI" and
                        suc_location.country_code == location.country_code
                ):
                    span_end = suc_usage['end']
                    usage['word'] = query[usage['start']:span_end]
                    usage['end'] = span_end
                    merged_locations.append((suc_location, suc_usage))

        return [x for x in locations if x not in merged_locations]

    def _resolve_alias(self, text):
        if text in _COUNTRY_ALIASES:
            return _COUNTRY_ALIASES[text]
        else:
            return text

    def _get_alternate_term(self, text):
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