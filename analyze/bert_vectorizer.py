from biobert_embedding.embedding import BiobertEmbedding
from .vectorizer import TextVectorizer
import numpy as np
from sentence_splitter import SentenceSplitter, split_text_into_sentences
from tqdm import tqdm
import os


class BioBertVectorizer(TextVectorizer):
    def __init__(self):
        self.splitter = SentenceSplitter(language='en')

    def vectorize(self, texts):
        model = BiobertEmbedding(model_path=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'biobert_v1.1_pubmed_pytorch_model'))
        vectors = []
        for text in tqdm(texts):
            sentences = self.splitter.split(text)
            vec = np.zeros(768)
            for sentence in sentences:
                result = model.sentence_vector(sentence).numpy()
                vec += result
            vectors.append(vec / len(sentences))
        return np.array(vectors)
