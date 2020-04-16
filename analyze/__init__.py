from .vectorizer import PretrainedLDA
from .similarity import JensonShannonSimilarity, CosineDistance
import os
from analyze.analyzer import CombinedPaperAnalyzer, BasicPaperAnalyzer

dir_path = os.path.dirname(os.path.realpath(__file__))

sentence_transformer_analyzer = None
lda_analyzer = None
topic_assignment_analyzer = None
paper_similarities_analyzer = None


def get_topic_assignment_analyzer():
    global topic_assignment_analyzer

    if not topic_assignment_analyzer:
        topic_assignment_analyzer = CombinedPaperAnalyzer(
            {
                "lda":
                    {
                        "analyzer": get_lda_analyzer(),
                        "weight": .5
                    },
                "title_sentence":
                    {
                        "analyzer": get_sentence_transformer_analyzer(),
                        "weight": .5
                    }
            }
        )

    return topic_assignment_analyzer


def get_paper_similarities_analyzer():
    global paper_similarities_analyzer

    if not paper_similarities_analyzer:
        paper_similarities_analyzer = CombinedPaperAnalyzer(
            {
                "lda":
                    {
                        "analyzer": get_lda_analyzer(),
                        "weight": 0.5
                    },
                "title_sentence":
                    {
                        "analyzer": get_sentence_transformer_analyzer(),
                        "weight": 0.5
                    }
            }
        )

    return paper_similarities_analyzer


def get_lda_analyzer():
    global lda_analyzer

    if not lda_analyzer:
        print("Initializing LDA Paper Analyzer")
        lda_analyzer = BasicPaperAnalyzer('lda')

    return lda_analyzer


def get_sentence_transformer_analyzer():
    global sentence_transformer_analyzer

    if not sentence_transformer_analyzer:
        print("Initializing Paper Analyzer")

        sentence_transformer_analyzer = BasicPaperAnalyzer('sentence-transformer')

    return sentence_transformer_analyzer
