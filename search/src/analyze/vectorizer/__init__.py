from .paper_vectorizer import PaperVectorizer
from .sentence_vectorizer import TitleSentenceVectorizer
from .transformer_paper_vectorizer import TransformerPaperVectorizer

vectorizers = dict()

def get_vectorizer(type):
    if type in vectorizers:
        return vectorizers[type]
    if type == 'title-sentence':
        vectorizers[type] = TitleSentenceVectorizer(matrix_file_name='title_sentence_vectorizer.pkl')
    elif type == 'transformer-paper':
        vectorizers[type] = TransformerPaperVectorizer(matrix_file_name='transformer_paper.pkl')
    else:
        raise ValueError("Unknown type")
    return vectorizers[type]
