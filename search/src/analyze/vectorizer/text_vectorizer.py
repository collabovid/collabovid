import joblib
import numpy as np
import os
from data.models import Paper
from django.conf import settings
from collabovid_store.auto_update_reference import AutoUpdateReference
from collabovid_store.stores import PaperMatrixStore, refresh_local_timestamps
from collabovid_store.s3_utils import S3BucketClient


class TextVectorizer:

    def __init__(self, matrix_file_name, *args, **kwargs):
        self.matrix_file_name = matrix_file_name
        self._similarity_computer = None
        self._paper_matrix_reference = AutoUpdateReference(base_path=settings.PAPER_MATRIX_DIR,
                                                           key=matrix_file_name, load_function=lambda x: joblib.load(x))

    @property
    def similarity_computer(self):
        if not self._similarity_computer:
            raise AttributeError("Similarity computer not set")
        return self._similarity_computer

    @similarity_computer.setter
    def similarity_computer(self, value):
        self._similarity_computer = value

    @property
    def paper_matrix(self):
        return self._paper_matrix_reference.reference

    def _calculate_paper_matrix(self, papers):
        matrix = self.vectorize_paper(papers)
        return {'matrix': matrix}

    def generate_paper_matrix(self, force_recompute=False):
        # initialize the id_map with saved values if possible
        if self.paper_matrix is not None:
            id_map = self.paper_matrix['id_map']
        else:
            id_map = {}

        # determines if a paper needs an update
        def needs_update(paper):
            return force_recompute

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
            for key, computed_matrix in self._calculate_paper_matrix(filtered_papers).items():
                # dimension of newly computed values
                matrix = np.zeros((newly_added, computed_matrix.shape[1]))

                if self.paper_matrix is not None:
                    # extend old matrix with dimensions of newly computed values
                    matrix = np.append(self.paper_matrix[key], computed_matrix, axis=0)

                for i, paper in enumerate(filtered_papers):
                    # get the matrix index for the computed value from the id map
                    matrix_idx = id_map[paper.doi]
                    # replace it with the new computed value
                    matrix[matrix_idx] = computed_matrix[i]
                paper_matrix[key] = matrix

            # Write out matrix
            joblib.dump(paper_matrix, os.path.join(settings.PAPER_MATRIX_DIR, self.matrix_file_name))
            refresh_local_timestamps(settings.PAPER_MATRIX_DIR, [self.matrix_file_name])
            if settings.PUSH_PAPER_MATRIX:
                self._update_remote_paper_matrix()

            print("Paper matrix exported completed")
        else:
            print("No recomputing of matrix necessary")

    def _update_remote_paper_matrix(self):
        aws_access_key = settings.AWS_ACCESS_KEY_ID
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        endpoint_url = settings.AWS_S3_ENDPOINT_URL
        s3_bucket_client = S3BucketClient(aws_access_key=aws_access_key, aws_secret_access_key=aws_secret_access_key,
                                          endpoint_url=endpoint_url, bucket=bucket)
        paper_matrix_store = PaperMatrixStore(s3_bucket_client)
        paper_matrix_store.update_remote(settings.PAPER_MATRIX_DIR, [self.matrix_file_name])

    def compute_similarity_scores(self, embedding_vec):
        matrix = self.paper_matrix['matrix']
        similarity_scores = self.similarity_computer.similarities(matrix, embedding_vec)
        return self.paper_matrix['index_arr'], similarity_scores

    def vectorize(self, texts):
        raise NotImplementedError()

    def vectorize_paper(self, paper):
        texts = [p.title + ". " + p.abstract for p in paper]
        return self.vectorize(texts)

    def vectorize_topics(self, topics):
        texts = [t.name + ". " + t.description for t in topics]
        return self.vectorize(texts)
