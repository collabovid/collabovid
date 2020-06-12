import joblib
from django.conf import settings
from collabovid_store.auto_update_reference import AutoUpdateReference
from .exceptions import *
from data.models import Paper
import numpy as np


class TextVectorizer:

    def __init__(self, matrix_file_name, similarity_computer, *args, **kwargs):
        self.matrix_file_name = matrix_file_name
        self._similarity_computer = similarity_computer
        self._paper_matrix_reference = AutoUpdateReference(base_path=settings.PAPER_MATRIX_BASE_DIR,
                                                           key=matrix_file_name, load_function=lambda x: joblib.load(x))

    def vectorize_query(self, query: str):
        raise NotImplementedError()

    def _compute_paper_matrix_contents(self, papers):
        raise NotImplementedError()

    def matching_to_query(self, query: str):
        embedding = self.vectorize_query(query)
        return self._compute_similarity_scores(embedding)

    def similar_to_paper(self, doi: str):
        matrix = self._paper_matrix['matrix']
        matrix_index = self._paper_matrix['id_map']['doi']
        return self._compute_similarity_scores(matrix[matrix_index])

    @property
    def _paper_matrix(self):
        matrix = self._paper_matrix_reference.reference
        if matrix is None:
            raise CouldNotLoadPaperMatrix(
                "Could not initialize with paper matrix file {}".format(self.matrix_file_name))
        return matrix

    def _compute_similarity_scores(self, embedding_vec):
        matrix = self._paper_matrix['matrix']
        similarity_scores = self._similarity_computer.similarities(matrix, embedding_vec)
        return self._paper_matrix['index_arr'], similarity_scores

    def compute_paper_matrix(self, force_recompute=False):
        old_paper_matrix = self._paper_matrix
        # initialize the id_map with saved values if possible
        if old_paper_matrix and not force_recompute:
            id_map = old_paper_matrix['id_map']
        else:
            id_map = {}

        # determines if a paper needs an update
        def needs_update(paper):
            return force_recompute

        if old_paper_matrix:
            print("Current paper matrix has size ", old_paper_matrix['matrix'].shape, "with",
                  Paper.objects.all().count(),
                  "in database")

        # all papers
        papers = Paper.objects.all()

        # papers that need to be recomputed
        filtered_papers = []

        # represents the index where the paper should be inserted in the final matrix
        new_matrix_idx = len(id_map)
        newly_added = 0
        for p in papers:
            if p.doi not in id_map:
                # paper was not in existing matrix, it needs recomputation and we will append the result
                id_map[p.doi] = new_matrix_idx
                filtered_papers.append(p)
                new_matrix_idx += 1
                newly_added += 1
            elif needs_update(p):
                # paper is in existing matrix, so just mark it for recomputing. An index is already saved in the id_map.
                filtered_papers.append(p)

        if len(filtered_papers) > 0:
            # construct index array based on id map
            index_arr = [''] * len(id_map)
            for doi, idx in id_map.items():
                index_arr[idx] = doi
            paper_matrix = {
                'id_map': id_map,
                'index_arr': index_arr,
            }

            # for every new embedding matrix that is computed, we extend the old one
            for key, computed_matrix in self._compute_paper_matrix_contents(filtered_papers).items():
                # dimension of newly computed values
                matrix = np.zeros((newly_added, computed_matrix.shape[1]))

                print("Matrix", matrix.shape)
                print("Computed Matrix", computed_matrix.shape)

                if old_paper_matrix and not force_recompute:
                    # extend old matrix with dimensions of newly computed values
                    matrix = np.append(old_paper_matrix[key], computed_matrix, axis=0)

                for i, paper in enumerate(filtered_papers):
                    # get the matrix index for the computed value from the id map
                    matrix_idx = id_map[paper.doi]
                    # replace it with the new computed value
                    matrix[matrix_idx] = computed_matrix[i]
                paper_matrix[key] = matrix

            return paper_matrix
        else:
            return old_paper_matrix
