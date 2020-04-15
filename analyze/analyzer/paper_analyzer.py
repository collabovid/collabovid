class PaperAnalyzer:
    def __init__(self, *args, **kwargs):
        pass

    def preprocess(self, force_recompute=False):
        raise NotImplementedError("Preprocess not implemented")

    def assign_to_topics(self):
        raise NotImplementedError("Assign to topics not implemented")

    def related(self, query: str):
        raise NotImplementedError("Related not implemented")

    def compute_topic_score(self, topics):
        raise NotImplementedError("Compute topic score not implemented")

    def query(self, query: str):
        raise NotImplementedError("Compute Similarity Scores not implemented")

    def get_similar_papers(self, paper_id: str):
        raise NotImplementedError("Compute Similarity Scores between papers not implemented")