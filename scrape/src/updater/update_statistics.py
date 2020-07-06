class UpdateStatistics:
    """
    Class that holds statistics for the update process.
    """
    def __init__(self):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0
        self.n_missing_datapoints = 0

        self.authors_deleted = 0
        self.journals_deleted = 0

        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = timer()

    def stop(self):
        self.end_time = timer()

    def __str__(self):
        s = []

        elapsed_time = timedelta(seconds=self.end_time - self.start_time)
        s.append(f"Time (total): {elapsed_time}")
        total_handled = self.n_success + self.n_errors
        if total_handled > 0:
            s.append(f"Time (per Record): {elapsed_time / total_handled}")
        s.append(f"Created/Updated: {self.n_success}")
        s.append(f"Skipped: {self.n_skipped}")
        s.append(f"Errors: {self.n_errors}")
        s.append(f"Missing Datapoints: {self.n_missing_datapoints}")
        s.append(f"Tracked by other source: {self.n_already_tracked}")
        s.append(f"Deleted Authors: {self.authors_deleted}")
        s.append(f"Deleted Journals: {self.journals_deleted}")

        return '\n'.join(s)
