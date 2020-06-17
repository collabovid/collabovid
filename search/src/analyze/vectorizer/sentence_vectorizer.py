import numpy as np
from sentence_transformers import SentenceTransformer
import os

from src.analyze.similarity import CosineSimilarity
from . import PaperVectorizer
from django.conf import settings
from .exceptions import CouldNotLoadModel


class TitleSentenceVectorizer(PaperVectorizer):
    """
    Utilizing the model from sentence-transformer (https://github.com/UKPLab/sentence-transformers)
    to vectorize sentences, i.e. titles of papers.
    """

    def __init__(self, matrix_file_name, *args, **kwargs):
        super(TitleSentenceVectorizer, self).__init__(matrix_file_name=matrix_file_name,
                                                      similarity_computer=CosineSimilarity(), *args, **kwargs)

    def _load_models(self):
        sentence_transformer_path = os.path.join(settings.MODELS_BASE_DIR, settings.SENTENCE_TRANSFORMER_MODEL_NAME)
        if not os.path.exists(sentence_transformer_path):
            raise CouldNotLoadModel("Could not load model from {}".format(sentence_transformer_path))
        self.model = SentenceTransformer(sentence_transformer_path, device='cpu')

    def vectorize_query(self, query: str):
        return self.model.encode([query])[0]

    def _compute_paper_matrix_contents(self, papers):
        matrix = np.array(self.model.encode([paper.title for paper in papers], batch_size=32, show_progress_bar=True))
        return {'matrix': matrix}
