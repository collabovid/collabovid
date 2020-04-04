import joblib
import en_core_sci_md
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_splitter import SentenceSplitter


class TextVectorizer:
    def vectorize(self, texts):
        raise NotImplementedError()

    def vectorize_paper(self, paper):
        texts = [p.title + ". " + p.abstract for p in paper]
        return self.vectorize(texts)

    def vectorize_topics(self, topics):
        texts = [t.name + ". " + t.description for t in topics]
        return self.vectorize(texts)


class PretrainedLDA(TextVectorizer):
    def __init__(self, lda_file, vectorizer_file):
        self.nlp = en_core_sci_md.load(disable=["tagger", "parser", "ner"])
        self.nlp.max_length = 2000000

        self.fix_imports()

        self.vectorizer = joblib.load(vectorizer_file)
        self.lda = joblib.load(lda_file)

    def fix_imports(self):
        def spacy_tokenizer(sentence):
            return [word.lemma_ for word in self.nlp(sentence) if
                    not (word.like_num or word.is_stop or word.is_punct or word.is_space or len(word) == 1)]

        # add missing
        setattr(sys.modules['__main__'], 'spacy_tokenizer', spacy_tokenizer)

    def vectorize(self, texts):
        vectors = self.vectorizer.transform(texts)
        return self.lda.transform(vectors)


class SentenceVectorizer(TextVectorizer):
    def __init__(self, model_name='roberta-large-nli-stsb-mean-tokens'):
        self.model = SentenceTransformer(model_name, device='cpu')
        self.splitter = SentenceSplitter(language='en')

    def vectorize(self, texts):
        return self.model.encode(texts)

    def vectorize_paper(self, papers):
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

        return 0.5 * title_embedding + 0.5 * np.array(abstract_embeddings)

    def vectorize_topics(self, topics):
        texts = [t.name for t in topics]
        return np.array(self.model.encode(texts))
