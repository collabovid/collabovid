import joblib
import en_core_sci_md
import sys
from src.analyze.similarity import JensonShannonSimilarity
from . import TextVectorizer
import os
from django.conf import settings


class PretrainedLDA(TextVectorizer):
    LDA_BASE_DIR = os.path.join(settings.BASE_DIR, "res/lda/")

    def __init__(self, lda_file=os.path.join(LDA_BASE_DIR, 'lda.pkl'),
                 vectorizer_file=os.path.join(LDA_BASE_DIR, 'vectorizer.pkl'),
                 matrix_file_name=os.path.join(LDA_BASE_DIR, 'paper_matrix.pkl'),
                 *args, **kwargs):

        super(PretrainedLDA, self).__init__(matrix_file_name=matrix_file_name, *args, **kwargs)

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

    def vectorize(self, texts):
        vectors = self.vectorizer.transform(texts)
        return self.lda.transform(vectors)
