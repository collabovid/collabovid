import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'covid19_publications.settings'

import django
django.setup()

from analyze import BasicPaperAnalyzer
from data.models import Topic, Paper
import numpy as np
from collections import defaultdict
from analyze.vectorizer import SentenceVectorizer
from tqdm import tqdm

sentence_vectorizer = SentenceVectorizer(matrix_file_name="paper_matrix_sentence_transformer.pkl",
                                         title_similarity_factor=1.0, abstract_similarity_factor=0.0)
lda = BasicPaperAnalyzer('lda')


topics = list(Topic.objects.all())

topic_scores = defaultdict(list)
topic_embeddings = lda.vectorizer.vectorize_topics(topics)
topic_title_embeddings, topic_description_embeddings = sentence_vectorizer.vectorize_topics(topics)

paper_dois = []
paper_contents = []

for paper in Paper.objects.all():

    if paper.data and paper.data.content:
        paper_dois.append(paper.doi)
        paper_contents.append(paper.data.content)

    paper.topic = None
    paper.save()

paper_contents_embed = lda.vectorizer.vectorize(paper_contents)

for idx, topic in enumerate(tqdm(topics)):
    similarities = lda.vectorizer.similarity_computer.similarities(np.array(paper_contents_embed), topic_embeddings[idx])

    paper_ids, bert_similarities = sentence_vectorizer.compute_similarity_scores(topic_title_embeddings[idx])

    bert_similarities = [x for _, x in sorted(zip(paper_ids,bert_similarities), key=lambda x: paper_dois.index(x[0]))]

    for id, content_score, title_score in zip(paper_dois, similarities, bert_similarities):
        topic_scores[id].append(np.array(content_score, dtype='float64') * .5 + np.array(title_score, dtype='float64') * .5)

for doi in paper_dois:
    paper = Paper.objects.get(doi=doi)
    topic_idx = np.argmax(topic_scores[paper.doi]).item()
    paper.topic = topics[topic_idx]
    paper.topic_score = topic_scores[paper.doi][topic_idx]
    paper.save()
