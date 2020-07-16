import joblib
from django.conf import settings
from collabovid_store.auto_update_reference import AutoUpdateReference
from .exceptions import *
from data.models import Paper
import numpy as np
from collabovid_store.stores import PaperMatrixStore, refresh_local_timestamps
from collabovid_store.s3_utils import S3BucketClient
import os


def load_paper_matrix(x):
    return joblib.load(x)


class PaperVectorizer:

    def __init__(self, matrix_file_name, similarity_computer, *args, **kwargs):
        self.matrix_file_name = matrix_file_name
        self._similarity_computer = similarity_computer
        self._paper_matrix_reference = AutoUpdateReference(base_path=settings.PAPER_MATRIX_BASE_DIR,
                                                           key=matrix_file_name, load_function=load_paper_matrix)
        self._is_initializing = False
        self._is_initialized = False

    def vectorize_query(self, query: str):
        """
        Vectorizes a given query string into a numpy vector of the vectorizer's embedding length
        :param query: a arbitrary query string
        :return:
        """
        raise NotImplementedError()

    def initialize_models(self):
        if not self._is_initializing:
            self._is_initializing = True
            self._load_models()
            self._is_initialized = True
            self._is_initializing = False

    def cleanup_models(self):
        self._is_initialized = False
        self._unload_models()

    def initializing_models(self):
        return self._is_initializing

    def models_initialized(self):
        return self._is_initialized

    def _load_models(self):
        pass

    def _unload_models(self):
        pass

    def _compute_paper_matrix_contents(self, papers):
        raise NotImplementedError()

    def matching_to_query(self, query: str):
        embedding = self.vectorize_query(query)
        return self._compute_similarity_scores(embedding)

    def similar_to_paper(self, doi: str):
        matrix = self.paper_matrix['matrix']
        matrix_index = self.paper_matrix['id_map'][doi]
        dois, scores = self._compute_similarity_scores(matrix[matrix_index])
        del scores[matrix_index]
        dois = dois[:matrix_index] + dois[matrix_index + 1:]
        return dois, scores

    def preprocess(self, force_recompute=False):
        paper_matrix = self.compute_paper_matrix(force_recompute=force_recompute)

        # Write out matrix
        joblib.dump(paper_matrix, os.path.join(settings.PAPER_MATRIX_BASE_DIR, self.matrix_file_name))
        refresh_local_timestamps(settings.PAPER_MATRIX_BASE_DIR, [self.matrix_file_name])
        if settings.PUSH_PAPER_MATRIX:
            self._update_remote_paper_matrix()
            print("Paper matrix exported completed")
        else:
            print("Not pushing matrix")

    @property
    def paper_matrix(self):
        matrix = self._paper_matrix_reference.reference
        if matrix is None:
            raise CouldNotLoadPaperMatrix(
                "Could not initialize with paper matrix file {}".format(self.matrix_file_name))
        return matrix

    def _compute_similarity_scores(self, embedding_vec):
        matrix = self.paper_matrix['matrix']
        similarity_scores = self._similarity_computer.similarities(matrix, embedding_vec)
        return self.paper_matrix['index_arr'], similarity_scores

    def _update_remote_paper_matrix(self):
        aws_access_key = settings.AWS_ACCESS_KEY_ID
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        endpoint_url = settings.AWS_S3_ENDPOINT_URL
        s3_bucket_client = S3BucketClient(aws_access_key=aws_access_key,
                                          aws_secret_access_key=aws_secret_access_key,
                                          endpoint_url=endpoint_url, bucket=bucket)
        paper_matrix_store = PaperMatrixStore(s3_bucket_client)
        paper_matrix_store.update_remote(settings.PAPER_MATRIX_BASE_DIR,
                                         [self.matrix_file_name.replace('.pkl', '')])

    def compute_paper_matrix(self, force_recompute=False):
        old_paper_matrix = self.paper_matrix

        if old_paper_matrix:
            print("Current paper matrix has size ", len(old_paper_matrix['index_arr']), "with",
                  Paper.objects.all().count(), "in database")

        # all papers
        papers = Paper.objects.all()

        id_map = {}
        if old_paper_matrix and not force_recompute:
            # delete papers from matrix that are not any more in the db
            dois = {paper.doi for paper in papers}
            indices_to_delete = []
            for idx, doi in enumerate(old_paper_matrix['index_arr']):
                if doi not in dois:
                    indices_to_delete.append(idx)

            print(f'Deleting {len(indices_to_delete)} Papers from matrix')

            # delete from matrix
            for key in old_paper_matrix.keys():
                if key not in ['index_arr', 'id_map']:
                    old_paper_matrix[key] = np.delete(old_paper_matrix[key], indices_to_delete, axis=0)

            # delete from index array
            for idx in reversed(indices_to_delete):
                del old_paper_matrix['index_arr'][idx]

            # initialize the id_map with saved values if possible
            for idx, doi in enumerate(old_paper_matrix['index_arr']):
                id_map[doi] = idx

            old_paper_matrix['id_map'] = id_map

        # determines if a paper needs an update
        def needs_update(paper):
            return force_recompute or not paper.vectorized

        # papers that need to be recomputed
        filtered_papers = []

        # represents the index where the paper should be inserted in the final matrix
        new_matrix_idx = len(id_map)
        newly_added = 0
        updated = 0
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
                updated += 1

        print(f'Newly added papers: {newly_added}')
        print(f'Paper that need an update: {updated}')

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
                    matrix = np.append(old_paper_matrix[key], matrix, axis=0)

                for i, paper in enumerate(filtered_papers):
                    # get the matrix index for the computed value from the id map
                    matrix_idx = id_map[paper.doi]
                    # replace it with the new computed value
                    matrix[matrix_idx] = computed_matrix[i]
                paper_matrix[key] = matrix

            return paper_matrix
        else:
            return old_paper_matrix
