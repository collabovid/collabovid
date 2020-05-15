import numpy as np
from sentence_transformers import SentenceTransformer
import os

from src.analyze.similarity import CosineDistance
from . import TextVectorizer
from django.conf import settings
from .exceptions import CouldNotLoadModel

class TitleSentenceVectorizer(TextVectorizer):
    """
    Utilizing the model from sentence-transformer (https://github.com/UKPLab/sentence-transformers)
    to vectorize sentences, i.e. titles of papers and topics.
    """

    def __init__(self, matrix_file_name="title_sentence_vectorizer.pkl", *args, **kwargs):
        super(TitleSentenceVectorizer, self).__init__(matrix_file_name=matrix_file_name, *args, **kwargs)

        self.similarity_computer = CosineDistance()

        sentence_transformer_path = os.path.join(settings.MODELS_BASE_DIR, settings.SENTENCE_TRANSFORMER_MODEL_NAME)

        if not os.path.exists(sentence_transformer_path):
            raise CouldNotLoadModel("Could not load model from {}".format(sentence_transformer_path))

        self.model = SentenceTransformer(sentence_transformer_path, device='cpu')

    def vectorize(self, texts):
        return self.model.encode(texts)

    def vectorize_paper(self, papers):
        return np.array(self.model.encode([paper.title for paper in papers], batch_size=32, show_progress_bar=True))

    def vectorize_topics(self, topics):
        return np.array(self.model.encode([t.name for t in topics]))
