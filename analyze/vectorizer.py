import joblib
import en_core_sci_md
import sys
import numpy as np
from sentence_transformers import SentenceTransformer


class TextVectorizer():
    def vectorize(self, texts):
        raise NotImplementedError()

    def vectorize_paper(self, paper):
        texts = [p.title + ". " + p.abstract for p in paper]
        return self.vectorize(texts)


nlp = en_core_sci_md.load(disable=["tagger", "parser", "ner"])
nlp.max_length = 2000000


def spacy_tokenizer(sentence):
    return [word.lemma_ for word in nlp(sentence) if
            not (word.like_num or word.is_stop or word.is_punct or word.is_space or len(word) == 1)]


# add missing
setattr(sys.modules['__main__'], 'spacy_tokenizer', spacy_tokenizer)


class PretrainedLDA(TextVectorizer):
    def __init__(self, lda_file, vectorizer_file):
        self.vectorizer = joblib.load(vectorizer_file)
        self.lda = joblib.load(lda_file)

    def vectorize(self, texts):
        vectors = self.vectorizer.transform(texts)
        return self.lda.transform(vectors)


class SentenceTransformerVectorizer(TextVectorizer):
    def __init__(self, model_name='roberta-large-nli-stsb-mean-tokens'):
        self.model = SentenceTransformer(model_name)

    def vectorize(self, texts):
        return self.model.encode(texts)

    def vectorize_paper(self, papers):
        titles = [paper.title for paper in papers]
        abstracts = [paper.abstract for paper in papers]
        title_embeds = self.model.encode(titles)
        abstract_embeds = self.model.encode(abstracts)
        embeds = 0.7 * np.array(title_embeds) + 0.3 * np.array(abstract_embeds)
        return embeds
