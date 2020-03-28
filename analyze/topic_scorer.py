import joblib

class TopicScorer:
    def score(self, texts):
        raise NotImplementedError()


class PretrainedLDA(TopicScorer):
    def __init__(self, lda_file, vectorizer):
        self.vectorizer = vectorizer
        self.lda = joblib.load(lda_file)

    def score(self, texts):
        vectors = self.vectorizer.vectorize(texts)
        return self.lda.transform(vectors)
