from .paper_vectorizer import PaperVectorizer
from .sentence_vectorizer import TitleSentenceVectorizer
from .transformer_paper_vectorizer import TransformerPaperVectorizer

vectorizers = dict()


def get_vectorizer(type) -> PaperVectorizer:
    if type in vectorizers:
        return vectorizers[type]
    if type == 'title-sentence':
        vectorizers[type] = TitleSentenceVectorizer(matrix_file_name='title_sentence_vectorizer.pkl')
    elif type == 'transformer-paper-oubiobert-512':
        vectorizers[type] = TransformerPaperVectorizer(matrix_file_name='transformer_paper_oubiobert_512.pkl',
                                                       transformer_model_name='transformer_paper_oubiobert_512',
                                                       transformer_model_type='bert')
    elif type == 'transformer-paper-sensitive-512':
        vectorizers[type] = TransformerPaperVectorizer(matrix_file_name='transformer_paper_sensitive_512.pkl',
                                                       transformer_model_name='transformer_paper_sensitive_512',
                                                       transformer_model_type='bert')
    elif type == 'transformer-paper-no-locations':
        vectorizers[type] = TransformerPaperVectorizer(matrix_file_name='transformer_paper_no_locations.pkl',
                                                       transformer_model_name='transformer_paper_no_locations',
                                                       transformer_model_type='bert')
    else:
        raise ValueError("Unknown type")
    return vectorizers[type]
