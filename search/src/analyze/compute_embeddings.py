from tasks.definitions import Runnable, register_task
from sklearn.manifold import TSNE
from . import get_vectorizer
from django.conf import settings
import json
from collabovid_store.s3_utils import S3BucketClient


@register_task
class ReduceEmbeddingDimensionality(Runnable):

    @staticmethod
    def task_name():
        return "reduce-embedding-dimensionality"

    def __init__(self, vectorizer_name: str = 'transformer-paper-oubiobert-512', *args, **kwargs):
        super(ReduceEmbeddingDimensionality, self).__init__(*args, **kwargs)
        self._vectorizer_name = vectorizer_name

    def run(self):
        self.log("Starting ReduceEmbeddingDimensionality")
        vectorizer = get_vectorizer(self._vectorizer_name)
        paper_matrix = vectorizer.paper_matrix
        X = 0.5 * paper_matrix['abstract'] + 0.5 * paper_matrix['title']
        points = TSNE(n_components=3).fit_transform(X)
        dois = paper_matrix['index_arr']
        result = []
        for i, doi in enumerate(dois):
            result.append({
                'doi': doi,
                'point': points[i].tolist(),
            })
        if settings.DEBUG:
            with open('../web/assets/embeddings_3d.json', 'w+') as f:
                json.dump(result, f)
        else:
            s3_bucket_client = S3BucketClient(aws_access_key=settings.AWS_ACCESS_KEY_ID,
                                              aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                              endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                                              bucket=settings.AWS_STORAGE_BUCKET_NAME)
            s3_bucket_client.upload_as_json('embeddings/embeddings_3d.json', result)

        self.log("ReduceEmbeddingDimensionality finished")
