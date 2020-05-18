import json
from os.path import join, exists
import dateutil.parser


class AutoUpdateReference():
    def __init__(self, base_path, key, load_function, timestamp_file='timestamps.json'):
        self._base_path = base_path
        self._key = key
        self._timestamp_file_path = join(self._base_path, timestamp_file)
        self._reference = None
        self._load_function = load_function
        self._timestamp = None

    @property
    def reference(self):
        if not exists(self._timestamp_file_path):
            return None

        with open(self._timestamp_file_path, 'r') as f:
            timestamp_data = json.load(f)
            if self._key not in timestamp_data:
                return None

            file_timestamp = dateutil.parser.parse(timestamp_data[self._key])
            if self._timestamp is None or file_timestamp > self._timestamp:
                self._reference = self._load_function(join(self._base_path, self._key))
                self._timestamp = file_timestamp

        return self._reference
