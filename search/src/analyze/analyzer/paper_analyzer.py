class PaperAnalyzer:
    def __init__(self, *args, **kwargs):
        pass

    def preprocess(self, force_recompute=False):
        raise NotImplementedError("preprocess not implemented")

    def similar(self, doi: str):
        raise NotImplementedError("similar not implemented")

    def query(self, query: str):
        raise NotImplementedError("query not implemented")
