import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--df', type=str, help='Path to dataframe csv', required=True)
args = parser.parse_args()

import django

django.setup()

import pandas as pd

from sklearn.feature_extraction import text
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

import en_core_sci_md
from data.models import Paper, PaperData
from tqdm import tqdm
import joblib

print('Reading Data from kaggle. Make sure cord19_df.csv exists...')
df = pd.read_csv(args.df)
cleaned_df = df['body_text'].dropna()
all_texts = list(cleaned_df)
print('Extracted {} texts from kaggle'.format(len(all_texts)))

print('Reading data from db...')
paper_data = PaperData.objects.all()
new_data = [data.content for data in paper_data]
print('Extracted {} texts from db'.format(len(new_data)))

all_texts += new_data

nlp = en_core_sci_md.load(disable=["tagger", "parser", "ner"])
nlp.max_length = 2000000


def spacy_tokenizer(sentence):
    return [word.lemma_ for word in nlp(sentence) if
            not (word.like_num or word.is_stop or word.is_punct or word.is_space or len(word) == 1)]


customize_stop_words = [
    'doi', 'preprint', 'copyright', 'peer', 'reviewed', 'org', 'https', 'et', 'al', 'author', 'figure',
    'rights', 'reserved', 'permission', 'used', 'using', 'biorxiv', 'fig', 'fig.', 'al.',
    'di', 'la', 'il', 'del', 'le', 'della', 'dei', 'delle', 'una', 'da', 'dell', 'non', 'si', 'funding'
    # 'covid-19', 'covid19', 'sars-cov-2', 'coronavirus'
]

# Mark them as stop words
for w in customize_stop_words:
    nlp.vocab[w].is_stop = True

print('Starting vectorizer....')
vectorizer = CountVectorizer(tokenizer=spacy_tokenizer, max_features=800000)
data_vectorized = vectorizer.fit_transform(tqdm(all_texts))
joblib.dump(vectorizer, 'vectorizer.pkl')
joblib.dump(data_vectorized, 'data_vectorized.pkl')

print('Vectorizer Done. Starting LDA...')

lda = LatentDirichletAllocation(n_components=50, random_state=0)
lda.fit(data_vectorized)
joblib.dump(lda, 'lda.pkl')

print('Done!')
