import os
import torch
from transformers import AutoTokenizer
import numpy as np
from src.analyze.similarity import EuclideanSimilarity
from src.analyze.models.utils import batch_iterator
from src.analyze.models.paper_embedding_model import PaperEmbeddingModel
from . import PaperVectorizer
from django.conf import settings
from .exceptions import CouldNotLoadModel
from tqdm import tqdm
from .utils.sliding_window_tokenizer import SlidingWindowTokenizer


class TransformerPaperVectorizer(PaperVectorizer):
    def __init__(self, matrix_file_name, device='cpu', transformer_model_name='transformer_paper_oubiobert_512',
                 transformer_model_type='bert', max_token_length=512, batch_size=8, *args, **kwargs):
        super(TransformerPaperVectorizer, self).__init__(matrix_file_name=matrix_file_name,
                                                         similarity_computer=EuclideanSimilarity(), *args, **kwargs)

        self._device = device
        self._max_token_length = max_token_length
        self._title_importance = 0.5
        self._batch_size = batch_size
        self._model = None

        self._transformer_model_name = transformer_model_name
        self._transformer_model_type = transformer_model_type

    def extract_paper_matrix(self, dois=None):
        """
        The method extracts the submatrix for a given doi.
        It must return a single (possibly)
        :param dois:
        :return:
        """
        if dois:
            indices = [self.paper_matrix['id_map'][doi] for doi in dois]
            matrix = 0.5 * self.paper_matrix['title'][indices, :] + 0.5 * self.paper_matrix['abstract'][indices, :]
        else:
            matrix = 0.5 * self.paper_matrix['title'] + 0.5 * self.paper_matrix['abstract']

        return matrix

    def _load_models(self):
        model_path = os.path.join(settings.MODELS_BASE_DIR, self._transformer_model_name)
        if not os.path.exists(model_path):
            raise CouldNotLoadModel("Could not load model from {}".format(model_path))
        self._model = PaperEmbeddingModel(model_path=model_path, model_type=self._transformer_model_type)
        self._tokenizer = AutoTokenizer.from_pretrained(model_path)
        self._sliding_window_tokenizer = SlidingWindowTokenizer(tokenizer=self._tokenizer,
                                                                device=self._device,
                                                                max_length=512,
                                                                overlap=64)
        self._model.to(self._device)
        self._model.eval()

    def _unload_models(self):
        self._model = None
        self._tokenizer = None

    def vectorize_query(self, query: str):
        tokens, _ = self._sliding_window_tokenizer.tokenize([query.lower()])
        with torch.no_grad():
            embedding = self._model(tokens)[0].detach().cpu().numpy()
        return embedding

    def _generate_embeddings(self, features):
        new_features = []
        for key in features.keys():
            for i, batch in enumerate(features[key].split(self._batch_size)):
                if i >= len(new_features):
                    new_features.append({})
                new_features[i][key] = batch
        result = []
        for batch in new_features:
            result.append(self._model(batch))
        embeddings = torch.cat(result, dim=0)
        return embeddings

    def _pool_embeddings(self, representations, end_index_array):
        i = 0
        result = []
        for end_index in end_index_array:
            result.append(torch.mean(representations[i:end_index], dim=0))
            i = end_index
        return torch.stack(result)

    def _compute_paper_matrix_contents(self, papers):
        title_matrix = None
        abstract_matrix = None
        for paper_batch in tqdm(batch_iterator(papers, batch_size=self._batch_size)):
            title_tokens, title_index_array = self._sliding_window_tokenizer.tokenize(
                [paper.title.lower() for paper in paper_batch])
            abstract_tokens, abstracts_index_array = self._sliding_window_tokenizer.tokenize(
                [paper.abstract.lower() for paper in paper_batch])
            with torch.no_grad():
                title_embeddings, abstract_embeddings = [
                    self._pool_embeddings(self._generate_embeddings(features), end_index_array).detach().cpu().numpy()
                    for features, end_index_array in
                    [(title_tokens, title_index_array), (abstract_tokens, abstracts_index_array)]]

            title_matrix = np.concatenate((title_matrix, title_embeddings),
                                          axis=0) if title_matrix is not None else title_embeddings
            abstract_matrix = np.concatenate((abstract_matrix, abstract_embeddings),
                                             axis=0) if abstract_matrix is not None else abstract_embeddings
        return {
            'title': title_matrix,
            'abstract': abstract_matrix
        }

    def similar_to_paper(self, doi: str):
        matrix_index = self.paper_matrix['id_map'][doi]

        title_matrix = self.paper_matrix['title']
        abstract_matrix = self.paper_matrix['abstract']
        title_similarity_scores = self._similarity_computer.similarities(title_matrix, abstract_matrix[matrix_index])
        abstract_similarity_scores = self._similarity_computer.similarities(abstract_matrix, title_matrix[matrix_index])

        combined_scores = 0.5 * title_similarity_scores + 0.5 * abstract_similarity_scores

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
