import joblib
import en_core_sci_md
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_splitter import SentenceSplitter
import os

from analyze.similarity import JensonShannonSimilarity, CosineDistance
from data.models import Paper


class TextVectorizer:

    VECTORIZE_DEFAULT = 0
    VECTORIZE_TOPIC = 1
    VECTORIZE_PAPER = 2

    def __init__(self, matrix_file_name, *args, **kwargs):
        self.matrix_file_name = matrix_file_name
        self._similarity_computer = None
        self._paper_matrix = None

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

        if not self._paper_matrix:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            matrix_path = os.path.join(dir_path, os.path.join('res', self.matrix_file_name))
            if os.path.exists(matrix_path):
                self._paper_matrix = joblib.load(matrix_path)

        return self._paper_matrix

    @paper_matrix.setter
    def paper_matrix(self, value):
        self._paper_matrix = value

    def _calculate_paper_matrix(self, papers):
        matrix = self._vectorize_paper(papers)
        print(matrix.shape)
        return {'matrix': matrix}

    def generate_paper_matrix(self):
        matrix_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   os.path.join('res', self.matrix_file_name))

        if os.path.exists(matrix_path):
            print(matrix_path, "exists, overwriting..")

        papers = Paper.objects.all()
        id_map = {}
        for index, p in enumerate(papers):
            id_map[p.doi] = index

        paper_matrix = {
            'id_map': id_map,
            'index_arr': [p.doi for p in papers],
        }

        self.paper_matrix = {**paper_matrix, **self._calculate_paper_matrix}

        joblib.dump(self.paper_matrix, matrix_path)

        print("Paper matrix exported completely")

    def compute_similarity_scores(self, query: str, vectorizer_type=VECTORIZE_DEFAULT):
        query_dist = self._vectorize([query])[0]
        matrix = self.paper_matrix['matrix']
        similarity_scores = self.similarity_computer.similarities(matrix, query_dist)
        return self.paper_matrix['index_arr'], similarity_scores

    def _vectorize_for_type(self, query, vectorizer_type):

        if vectorizer_type == TextVectorizer.VECTORIZE_DEFAULT:
            if isinstance(query, str):
                return self._vectorize([query])[0]
            return self._vectorize(query)
        elif vectorizer_type == TextVectorizer.VECTORIZE_PAPER:
            return self._vectorize_paper(query)
        elif vectorizer_type == TextVectorizer.VECTORIZE_TOPIC:
            return self._vectorize_topics(query)
        else:
            raise ValueError("Invalid vectorizer type")

    def _vectorize(self, texts):
        raise NotImplementedError()

    def _vectorize_paper(self, paper):
        texts = [p.title + ". " + p.abstract for p in paper]
        return self._vectorize(texts)

    def _vectorize_topics(self, topics):
        texts = [t.name + ". " + t.description for t in topics]
        return self._vectorize(texts)


class PretrainedLDA(TextVectorizer):
    def __init__(self, lda_file, vectorizer_file, *args, **kwargs):
        super(PretrainedLDA, self).__init__(*args, **kwargs)

        self.nlp = en_core_sci_md.load(disable=["tagger", "parser", "ner"])
        self.nlp.max_length = 2000000

        self.fix_imports()

        self.vectorizer = joblib.load(vectorizer_file)
        self.lda = joblib.load(lda_file)

        self.similarity_computer = JensonShannonSimilarity()

    def fix_imports(self):
        def spacy_tokenizer(sentence):
            return [word.lemma_ for word in self.nlp(sentence) if
                    not (word.like_num or word.is_stop or word.is_punct or word.is_space or len(word) == 1)]

        # add missing
        setattr(sys.modules['__main__'], 'spacy_tokenizer', spacy_tokenizer)

    def _vectorize(self, texts):
        vectors = self.vectorizer.transform(texts)
        return self.lda.transform(vectors)


class SentenceVectorizer(TextVectorizer):
    def __init__(self, model_name='roberta-large-nli-stsb-mean-tokens', *args, **kwargs):
        super(SentenceVectorizer, self).__init__(*args, **kwargs)

        self.model = SentenceTransformer(model_name, device='cpu')
        self.splitter = SentenceSplitter(language='en')

        self.similarity_computer = CosineDistance()

    def compute_similarity_scores(self, query, vectorizer_type=TextVectorizer.VECTORIZE_DEFAULT):

        query_dist = self._vectorize_for_type(query, vectorizer_type)

        title_matrix = self.paper_matrix['title_matrix']
        abstract_matrix = self.paper_matrix['abstract_matrix']

        title_similarity_scores = np.array(self.similarity_computer.similarities(title_matrix, query_dist))
        abstract_similarity_scores = np.array(self.similarity_computer.similarities(abstract_matrix, query_dist))

        return self.paper_matrix['index_arr'], title_similarity_scores * 0.7 + abstract_similarity_scores * 0.3

    def _vectorize(self, texts):
        return self.model.encode(texts)

    def _vectorize_paper(self, papers):
        abstract_embeddings = []

        all_sentences = []
        positions = []

        for paper in papers:
            sentences = self.splitter.split(paper.abstract)

            start = len(all_sentences)
            length = len(sentences)

            all_sentences += sentences

            positions.append((start, length))

        print("Extracted all sentences, calculating embedding")
        sentence_embeddings = self.model.encode(all_sentences, batch_size=32, show_progress_bar=True)

        print("Extracting Embedding")

        for start, length in positions:
            if length == 0:
                abstract_embeddings.append(np.zeros(1024))
            else:
                abstract_embeddings.append(np.mean(np.array(sentence_embeddings[start:length]), axis=0))

        print("Calculate Title Embedding")

        title_embedding = np.array(self.model.encode([paper.title for paper in papers], show_progress_bar=True))

        return title_embedding, np.array(abstract_embeddings)

    def _vectorize_topics(self, topics):
        texts = [t.name for t in topics]
        return np.array(self.model.encode(texts))

    def _calculate_paper_matrix(self, papers):

        title_embeddings, abstract_embeddings = self._vectorize_paper(papers)

        print('title embeddings', title_embeddings.shape)
        print('abstract embeddings', abstract_embeddings.shape)
        return {'title_matrix': title_embeddings, 'abstract_matrix': abstract_embeddings}
