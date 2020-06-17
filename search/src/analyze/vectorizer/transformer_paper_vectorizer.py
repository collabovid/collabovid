import os
import torch
from transformers import AutoTokenizer
from src.analyze.similarity import EuclideanSimilarity
from src.analyze.models.paper_embedding_model import PaperEmbeddingModel
from . import PaperVectorizer
from django.conf import settings
from .exceptions import CouldNotLoadModel

TRANSFORMER_MODEL_NAME = 'biobert'
TRANSFORMER_MODEL_TYPE = 'bert'


class TransformerPaperVectorizer(PaperVectorizer):
    def __init__(self, matrix_file_name, device='cpu', max_token_length=32, *args, **kwargs):
        super(TransformerPaperVectorizer, self).__init__(matrix_file_name=matrix_file_name,
                                                         similarity_computer=EuclideanSimilarity(), *args, **kwargs)

        self._device = device
        self._max_token_length = max_token_length
        self._title_importance = 0.5
        self._model = None

    def _load_models(self):
        model_path = os.path.join(settings.MODELS_BASE_DIR, TRANSFORMER_MODEL_NAME)
        if not os.path.exists(model_path):
            raise CouldNotLoadModel("Could not load model from {}".format(model_path))
        self._model = PaperEmbeddingModel(model_path=model_path, model_type=TRANSFORMER_MODEL_TYPE)
        self._tokenizer = AutoTokenizer.from_pretrained(model_path)
        self._model.to(self._device)
        self._model.eval()

    def vectorize_query(self, query: str):
        tokens = self._tokenize([query])
        with torch.no_grad():
            embedding = self._model(tokens)[0].detach().cpu().numpy()
        return embedding

    def _compute_paper_matrix_contents(self, papers):
        titles = [paper.title for paper in papers]
        abstracts = [paper.abstract for paper in papers]
        title_embeddings, abstract_embeddings = [self._model(self._tokenize(x)) for x in [titles, abstracts]]
        return {
            'title': title_embeddings,
            'abstract': abstract_embeddings
        }

    def similar_to_paper(self, doi: str):
        matrix_index = self.paper_matrix['id_map'][doi]

        title_matrix = self.paper_matrix['title']
        abstract_matrix = self.paper_matrix['abstract']
        title_similarity_scores = self._similarity_computer.similarities(title_matrix, abstract_matrix[matrix_index])
        abstract_similarity_scores = self._similarity_computer.similarities(abstract_matrix, title_matrix[matrix_index])

        combined_scores = self._title_importance * title_similarity_scores + (
                1 - self._title_importance) * abstract_similarity_scores

        scores = combined_scores.tolist()
        del scores[matrix_index]
        dois = self.paper_matrix['index_arr'][:matrix_index] + self.paper_matrix['index_arr'][matrix_index + 1:]
        return dois, scores

    def _compute_similarity_scores(self, embedding_vec):
        title_matrix = self.paper_matrix['title']
        title_similarity_scores = self._similarity_computer.similarities(title_matrix, embedding_vec)
        abstract_matrix = self.paper_matrix['abstract']
        abstract_similarity_scores = self._similarity_computer.similarities(abstract_matrix, embedding_vec)
        combined_scores = self._title_importance * title_similarity_scores + (
                1 - self._title_importance) * abstract_similarity_scores
        return self.paper_matrix['index_arr'], combined_scores.tolist()

    def _tokenize(self, items):
        tokens = self._tokenizer.batch_encode_plus(items, add_special_tokens=True, return_tensors='pt',
                                                   pad_to_max_length=True, return_attention_masks=True,
                                                   max_length=self._max_token_length)
        for key in list(tokens.keys()):
            tokens[key] = tokens[key].to(self._device)
        return tokens
