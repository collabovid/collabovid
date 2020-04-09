import numpy as np
from sentence_transformers import SentenceTransformer
import os

from analyze.similarity import CosineDistance
from . import TextVectorizer
from analyze.vectorizer.utils.splitter import TextToChunksSplitter
from django.conf import settings


class TitleSentenceVectorizer(TextVectorizer):
    """
    Utilizing the model from sentence-transformer (https://github.com/UKPLab/sentence-transformers)
    to vectorize sentences, i.e. titles of papers and topics.
    """
    TITLE_SENTENCE_VECTORIZER_BASE_DIR = os.path.join(settings.BASE_DIR, "analyze/res/title_sentence_vectorizer/")

    def __init__(self,
                 model_name='roberta-large-nli-stsb-mean-tokens',
                 matrix_file_name=os.path.join(TITLE_SENTENCE_VECTORIZER_BASE_DIR, "paper_matrix.pkl"),
                 *args, **kwargs):
        super(TitleSentenceVectorizer, self).__init__(matrix_file_name=matrix_file_name, *args, **kwargs)

        self.similarity_computer = CosineDistance()
        self.model = SentenceTransformer(model_name, device='cpu')

    def vectorize(self, texts):
        return self.model.encode(texts)

    def vectorize_paper(self, papers):
        return np.array(self.model.encode([paper.title for paper in papers], batch_size=32, show_progress_bar=True))

    def vectorize_topics(self, topics):
        return np.array(self.model.encode([t.name for t in topics]))


class SentenceChunkVectorizer(TextVectorizer):
    SENTENCE_CHUNK_VECTORIZER_BASE_DIR = os.path.join(settings.BASE_DIR, "analyze/res/sentence_chunk_vectorizer/")

    def __init__(self, model_name='roberta-large-nli-stsb-mean-tokens',
                 title_similarity_factor=0.5,
                 abstract_similarity_factor=0.5,
                 matrix_file_name=os.path.join(SENTENCE_CHUNK_VECTORIZER_BASE_DIR, "paper_matrix.pkl"),
                 *args, **kwargs):
        super(SentenceChunkVectorizer, self).__init__(matrix_file_name=matrix_file_name, *args, **kwargs)

        device = os.getenv('SENTENCE_TRANSFORMER_DEVICE', 'cpu')

        self.model = SentenceTransformer(model_name, device=device)
        self.splitter = TextToChunksSplitter()

        self.similarity_computer = CosineDistance()

        self.title_similarity_factor = title_similarity_factor
        self.abstract_similarity_factor = abstract_similarity_factor

    def compute_similarity_scores(self, embedding_vec):
        title_matrix = self.paper_matrix['title_matrix']
        abstract_matrix = self.paper_matrix['abstract_matrix']

        title_similarity_scores = np.array(self.similarity_computer.similarities(title_matrix, embedding_vec))
        abstract_similarity_scores = np.array(self.similarity_computer.similarities(abstract_matrix, embedding_vec))

        return self.paper_matrix['index_arr'], title_similarity_scores * self.title_similarity_factor + \
               abstract_similarity_scores * self.abstract_similarity_factor

    def vectorize(self, texts):
        return self.model.encode(texts)

    def vectorize_paper(self, papers):
        abstract_embeddings = []

        all_chunks = []
        positions = []

        for paper in papers:
            chunks = self.splitter.split_into_chunks(paper.abstract)
            start = len(all_chunks)
            length = len(chunks)
            all_chunks += chunks
            positions.append((start, length))

        print("Extracted all sentences, calculating embedding")
        chunk_embeddings = self.model.encode(all_chunks, batch_size=32, show_progress_bar=True)

        print("Extracting Embedding")

        for start, length in positions:
            if length == 0:
                abstract_embeddings.append(np.zeros(1024))
            else:
                abstract_embeddings.append(np.mean(np.array(chunk_embeddings[start:start + length]), axis=0))

        print("Calculate Title Embedding")

        title_embedding = np.array(self.model.encode([paper.title for paper in papers], show_progress_bar=True))

        return title_embedding, np.array(abstract_embeddings)

    def vectorize_topics(self, topics):

        all_chunks = []
        positions = []

        for topic in topics:
            chunks = self.splitter.split_into_chunks(topic.description)
            start = len(all_chunks)
            length = len(chunks)
            all_chunks += chunks
            positions.append((start, length))

        chunk_embeddings = self.model.encode(all_chunks, batch_size=32, show_progress_bar=True)

        description_embeddings = list()

        for start, length in positions:
            if length == 0:
                description_embeddings.append(np.zeros(1024))
            else:
                description_embeddings.append(chunk_embeddings[start:start + length])

        title_embeddings = np.array(self.model.encode([t.name for t in topics]))

        return title_embeddings, np.array(description_embeddings)

    def _calculate_paper_matrix(self, papers):

        title_embeddings, abstract_embeddings = self.vectorize_paper(papers)

        print('title embeddings', title_embeddings.shape)
        print('abstract embeddings', abstract_embeddings.shape)
        return {'title_matrix': title_embeddings, 'abstract_matrix': abstract_embeddings}
