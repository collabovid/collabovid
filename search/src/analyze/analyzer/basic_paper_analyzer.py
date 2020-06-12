from . import PaperAnalyzer
import joblib
import os
from django.conf import settings
from collabovid_store.stores import PaperMatrixStore, refresh_local_timestamps
from collabovid_store.s3_utils import S3BucketClient
import heapq


class BasicPaperAnalyzer(PaperAnalyzer):
    TYPE_SENTENCE_TRANSFORMER = 'sentence-transformer'
    TYPE_TRANSFORMER_PAPER = 'transformer-paper'

    def __init__(self, type=TYPE_SENTENCE_TRANSFORMER, *args, **kwargs):
        super(BasicPaperAnalyzer, self).__init__(*args, **kwargs)
        self.type = type
        if type == BasicPaperAnalyzer.TYPE_SENTENCE_TRANSFORMER:
            from src.analyze.vectorizer import TitleSentenceVectorizer
            self._matrix_file_name = "title_sentence_vectorizer.pkl"
            self._vectorizer = TitleSentenceVectorizer(matrix_file_name=self._matrix_file_name)
            print("Loaded paper matrix title sentence transformer")
        elif type == BasicPaperAnalyzer.TYPE_TRANSFORMER_PAPER:
            from src.analyze.vectorizer import TransformerPaperVectorizer
            self._matrix_file_name = "transformer_paper.pkl"
            self._vectorizer = TransformerPaperVectorizer(matrix_file_name=self._matrix_file_name)

    def query(self, query: str):
        indices, scores = self._vectorizer.matching_to_query(query)
        return list(zip(indices, scores))

    def similar(self, doi: str):
        indices, scores = self._vectorizer.similar_to_paper(doi)
        results = list(filter(lambda x: x[0] != doi, sorted(zip(indices, scores), key=lambda x: x[1], reverse=True)))
        return results

    def preprocess(self, force_recompute=False):
        paper_matrix = self._vectorizer.compute_paper_matrix(force_recompute=force_recompute)

        # Write out matrix
        joblib.dump(paper_matrix, os.path.join(settings.PAPER_MATRIX_BASE_DIR, self._matrix_file_name))
        refresh_local_timestamps(settings.PAPER_MATRIX_BASE_DIR, [self._matrix_file_name])
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
        s3_bucket_client = S3BucketClient(aws_access_key=aws_access_key,
                                          aws_secret_access_key=aws_secret_access_key,
                                          endpoint_url=endpoint_url, bucket=bucket)
        paper_matrix_store = PaperMatrixStore(s3_bucket_client)
        paper_matrix_store.update_remote(settings.PAPER_MATRIX_BASE_DIR,
                                         [self._matrix_file_name.replace('.pkl', '')])
