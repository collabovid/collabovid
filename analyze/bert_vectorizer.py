from biobert_embedding.embedding import BiobertEmbedding
from .vectorizer import TextVectorizer
import numpy as np
from sentence_splitter import SentenceSplitter
from tqdm import tqdm
import os


class BioBertVectorizer(TextVectorizer):
    def __init__(self):
        self.splitter = SentenceSplitter(language='en')
        self.model = BiobertEmbedding(
            model_path=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'biobert_v1.1_pubmed_pytorch_model'))

    def vectorize(self, texts):
        vectors = []
        for text in tqdm(texts):
            sentences = self.splitter.split(text)
            vec = np.zeros(768)
            for sentence in sentences:
                result = self.model.sentence_vector(sentence).numpy()
                vec += result
            vectors.append(vec / len(sentences))
        return np.array(vectors)

    def vectorize_paper(self, paper):
        vectors = []
        for p in tqdm(paper):
            title_vector = self.model.sentence_vector(p.title).numpy()
            sentences = self.splitter.split(p.abstract)
            vec = np.zeros(768)
            for sentence in sentences:
                vec += self.model.sentence_vector(sentence).numpy()
            result = 0.5 * title_vector + 0.5 * (vec / len(sentences))
            vectors.append(result)
        return np.array(vectors)
