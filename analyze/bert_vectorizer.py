from biobert_embedding.embedding import BiobertEmbedding
from .vectorizer import TextVectorizer
import numpy as np


class BioBertVectorizer(TextVectorizer):
    def vectorize(self, texts):
        model = BiobertEmbedding()
        vectors = []
        for text in texts:
            vec = model.sentence_vector(text).numpy()
            vectors.append(vec)
        return np.array(vectors)
