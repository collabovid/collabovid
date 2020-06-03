import json
from datetime import datetime, timedelta
from io import BytesIO
from timeit import default_timer as timer

import pysftp

class ElsevierSFTP:
    def __init__(self, ignorelist = None, log=print):
        self.sftp = None
        self.log = log
        if not ignorelist:
            self.ignore_list = []

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.sftp:
            self.sftp.close()
            self.sftp = None

    def connect(self):
        if not self.sftp:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            self.sftp = pysftp.Connection(
                "coronacontent.np.elsst.com",
                username="public",
                password="beat_corona",
                cnopts=cnopts,
            )

    def _getfile(self, filename):
        flo = BytesIO()
        self.sftp.getfo(f'{filename}', flo)
        flo.seek(0)
        return flo

    def _getfilecontent(self, filename):
        file = self._getfile(filename)
        content = file.read().decode("utf-8")
        file.close()
        return content

    def get_metadata(self):
        if not self.sftp:
            raise Exception("Elsevier SFTP connection not open")

        metadata_index = self._getfilecontent("_index_meta.txt").splitlines()
        start = timer()
        metadata = {}

        for i, line in enumerate(metadata_index[1:]): # Skip header
            if timer() - start > 120:
                print(metadata)
                exit()
            print(i)
            line_split = line.split(",")
            last_updated = datetime.strptime(line_split[1].strip(), "%Y-%m-%d %H:%M:%S+00:00")
            filename = line_split[0].strip()

            file = self._getfilecontent(filename)
            try:
                content = json.loads(file)["full-text-retrieval-response"]
                content["last_udated"] = last_updated

                metadata[content["coredata"]["prism:doi"].strip()] = content

            except json.decoder.JSONDecodeError:
                self.log(f"JSON parse error in {filename}")
            except KeyError:
                self.log(f"Found no DOI in JSON file {filename}")

        return metadata


if __name__ == '__main__':
    start = timer()
    with ElsevierSFTP() as elsevier:
        metadata = elsevier.get_metadata()
    end = timer()
    print(timedelta(seconds=end-start))