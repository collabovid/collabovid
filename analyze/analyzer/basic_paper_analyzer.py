from analyze.vectorizer import PretrainedLDA
import os

import numpy as np
from django.db import models
from collections import defaultdict
from data.models import Paper, Topic
from . import PaperAnalyzer

from django.conf import settings


class BasicPaperAnalyzer(PaperAnalyzer):

    TYPE_LDA = 'lda'
    TYPE_SENTENCE_TRANSFORMER = 'sentence-transformer'
    TYPE_CHUNK_SENTENCE_TRANSFORMER = 'chunk-sentence-transformer'

    def __init__(self, type=TYPE_LDA, *args, **kwargs):

        super(BasicPaperAnalyzer, self).__init__(*args, **kwargs)
        dir_path = os.path.join(settings.BASE_DIR, "analyze/res")

        self.type = type

        if type == BasicPaperAnalyzer.TYPE_LDA:
            self.vectorizer = PretrainedLDA()
            print("Loaded lda vectorizer")
        elif type == BasicPaperAnalyzer.TYPE_SENTENCE_TRANSFORMER:
            from analyze.vectorizer import TitleSentenceVectorizer
            self.vectorizer = TitleSentenceVectorizer()
            print("Loaded paper matrix title sentence transformer")
        elif type == BasicPaperAnalyzer.TYPE_CHUNK_SENTENCE_TRANSFORMER:
            from analyze.vectorizer import SentenceChunkVectorizer
            self.vectorizer = SentenceChunkVectorizer()
            print("Loaded paper matrix chunk sentence transformer")
        else:
            raise ValueError('Unknown type')

    def preprocess(self, force_recompute=False):
        self.vectorizer.generate_paper_matrix(force_recompute)

    def query(self, query: str):
        embedding = self.vectorizer.vectorize([query])[0]
        return self.vectorizer.compute_similarity_scores(embedding)

    def assign_to_topics(self):

        print("Assigning to topics")

        print("Matrix not empty")
        topics = list(Topic.objects.all())
        print("Beginning Paper assignment")

        topic_scores = self.compute_topic_score(topics)

        papers = Paper.objects.all()
        for paper in papers:
            topic_idx = np.argmax(topic_scores[paper.doi]).item()
            paper.topic = topics[topic_idx]
            paper.topic_score = topic_scores[paper.doi][topic_idx]
            paper.save()

        for topic in topics:
            topic.save()

        print("Finished asignment to topics")

    def related(self, query: str):
        paper_ids, scores = self.query(query)

        papers = Paper.objects.filter(pk__in=paper_ids)
        whens = list()

        for pk, score in zip(paper_ids, scores):
            whens.append(models.When(pk=pk, then=score * 100))

        papers = papers.annotate(search_score=models.Case(*whens, output_field=models.FloatField()))

        return papers

    def compute_topic_score(self, topics):
        if self.vectorizer.paper_matrix is None:
            raise Exception("Paper matrix empty")

        if self.type == BasicPaperAnalyzer.TYPE_CHUNK_SENTENCE_TRANSFORMER:
            topic_scores = self._topics_scores_chunk_sentence_transformer(topics)
        else:
            topic_scores = defaultdict(list)
            topic_embeddings = self.vectorizer.vectorize_topics(topics)

            for idx, topic in enumerate(topics):
                paper_ids, similarities = self.vectorizer.compute_similarity_scores(topic_embeddings[idx])

                for id, score in zip(paper_ids, similarities):
                    topic_scores[id].append(score)

        return topic_scores

    def _topics_scores_chunk_sentence_transformer(self, topics):
        topic_scores = defaultdict(list)
        topic_title_embeddings, topic_description_embeddings = self.vectorizer.vectorize_topics(topics)

        for idx, topic in enumerate(topics):

            paper_ids, title_similarities = self.vectorizer.compute_similarity_scores(topic_title_embeddings[idx])

            description_similarities_raw = list()

            for vec in topic_description_embeddings[idx]:
                _, similarities = self.vectorizer.compute_similarity_scores(vec)
                description_similarities_raw.append(similarities)

            description_similarities = np.array([sum(similarities_for_paper) / len(similarities_for_paper)
                                                 for similarities_for_paper in zip(*description_similarities_raw)])
            title_similarities = np.array(title_similarities)

            similarities = .5 * title_similarities + 0.5 * description_similarities

            for id, score in zip(paper_ids, similarities):
                topic_scores[id].append(score)

        return topic_scores
