import django

django.setup()

import numpy as np
import itertools
from data.models import Topic, Paper
from matplotlib import pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import KernelPCA
from sklearn.metrics import pairwise_distances

from analyze import get_sentence_transformer_analyzer


def get_vector_for_doi(analyzer, doi):
    index = analyzer.vectorizer.paper_matrix['id_map'][doi]
    return analyzer.vectorizer.paper_matrix['title_matrix'][index], analyzer.vectorizer.paper_matrix['abstract_matrix'][
        index]


def compute_distance_statistics(analyzer, iterator, name):
    distances = [1-analyzer.vectorizer.similarity_computer.similarities(np.array([center1]), center2)[0] for center1, center2
                 in iterator]
    print("Topic inter", name, "min/max/avg", min(distances), max(distances), sum(distances)/len(distances))

    return sum(distances)/len(distances)


def topic_discordance(analyzer):
    centers_titles = list()
    centers_abstracts = list()

    intra_title_avg = 0.0
    intra_abstract_avg = 0.0

    for topic in Topic.objects.all():
        papers = topic.papers
        title_matrix, abstract_matrix = list(zip(*[get_vector_for_doi(analyzer, p.doi) for p in papers.all()]))

        title_center = np.mean(np.array(title_matrix), axis=0)
        abstract_center = np.mean(np.array(abstract_matrix), axis=0)

        centers_titles.append(title_center)
        centers_abstracts.append(abstract_center)

        title_center_similarities = analyzer.vectorizer.similarity_computer.similarities(title_matrix, title_center)
        abstract_center_similarities = \
            analyzer.vectorizer.similarity_computer.similarities(abstract_matrix, abstract_center)

        title_center_similarities = [1-val for val in title_center_similarities]
        abstract_center_similarities = [1-val for val in abstract_center_similarities]

        print("Topic", topic.pk, " intra title min/max/avg", min(title_center_similarities),
              max(title_center_similarities), np.mean(title_center_similarities))
        print("Topic", topic.pk, " intra abstract min/max/avg", min(abstract_center_similarities),
              max(abstract_center_similarities), np.mean(abstract_center_similarities))

        intra_title_avg += sum(title_center_similarities) / (len(title_center_similarities) * Topic.objects.all().count())
        intra_abstract_avg += sum(abstract_center_similarities) / (len(abstract_center_similarities) * Topic.objects.all().count())

    title_centers_combinations = itertools.combinations(centers_titles, 2)
    abstract_centers_combinations = itertools.combinations(centers_abstracts, 2)

    inter_title_avg = compute_distance_statistics(analyzer, title_centers_combinations, "Title")
    inter_abstract_avg = compute_distance_statistics(analyzer, abstract_centers_combinations, "Abstract")

    return intra_title_avg, intra_abstract_avg, inter_title_avg, inter_abstract_avg

sentence_transformer_analyzer = get_sentence_transformer_analyzer()

#title_factor_values = [0.0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0]
title_factor_values = [0.0, 0.5, 1.0]

intra_title_avgs = list()
intra_abstract_avgs = list()
inter_title_avgs = list()
inter_abstract_avgs = list()

perplexity = 5

def get_dim_reduction_tsne():
    X = sentence_transformer_analyzer.vectorizer.paper_matrix['title_matrix']
    distance_matrix = pairwise_distances(X, X, metric='cosine')
    tsne = TSNE(metric='precomputed', n_components=2, verbose=1, perplexity=perplexity, n_iter=300)
    tsne_title_results = tsne.fit_transform(distance_matrix)

    X = sentence_transformer_analyzer.vectorizer.paper_matrix['abstract_matrix']
    distance_matrix = pairwise_distances(X, X, metric='cosine')
    tsne = TSNE(metric='precomputed', n_components=2, verbose=1, perplexity=perplexity, n_iter=300)
    tsne_abstract_results = tsne.fit_transform(distance_matrix)

    return tsne_title_results, tsne_abstract_results

def get_dim_reduction_pca():
    tsne = KernelPCA(kernel='cosine', n_components=2)
    pca_title_results = tsne.fit_transform(sentence_transformer_analyzer.vectorizer.paper_matrix['title_matrix'])

    tsne = KernelPCA(kernel='cosine', n_components=2)
    pca_abstract_results = tsne.fit_transform(sentence_transformer_analyzer.vectorizer.paper_matrix['abstract_matrix'])

    return pca_title_results, pca_abstract_results

#dim_reduced_titles, dim_reduced_abstracts = get_dim_reduction_tsne()
dim_reduced_titles, dim_reduced_abstracts = get_dim_reduction_pca()

for factor in title_factor_values:
    sentence_transformer_analyzer.vectorizer.title_similarity_factor = factor
    sentence_transformer_analyzer.vectorizer.abstract_similarity_factor = 1 - factor
    sentence_transformer_analyzer.assign_to_topics()
#
    #intra_title_avg, intra_abstract_avg, inter_title_avg, inter_abstract_avg = topic_discordance(analyzer)
#
    #intra_title_avgs.append(intra_title_avg)
    #intra_abstract_avgs.append(intra_abstract_avg)
    #inter_title_avgs.append(inter_title_avg)
    #inter_abstract_avgs.append(inter_abstract_avg)

    topics = list(Topic.objects.all())
    #tsne_abstract_results = tsne.fit_transform(analyzer.vectorizer.paper_matrix['abstract_matrix'])

    topics_for_index = [(paper.topic.pk,
                         sentence_transformer_analyzer.vectorizer.paper_matrix['id_map'][paper.doi])
              for paper in Paper.objects.all()]

    topics_for_index = sorted(topics_for_index, key=lambda x: x[1])

    colors = [color for color, idx in topics_for_index]

    plt.scatter(
        list(dim_reduced_titles[:, 0]),
        list(dim_reduced_titles[:, 1]), c=colors, cmap='Set1', alpha=.3)
    plt.title("Title title influence: " + str(sentence_transformer_analyzer.vectorizer.title_similarity_factor))
    plt.show()

    plt.scatter(
        list(dim_reduced_abstracts[:, 0]),
        list(dim_reduced_abstracts[:, 1]), c=colors, cmap='Set1', alpha=.3)
    plt.title("Abstracts title influence: " + str(sentence_transformer_analyzer.vectorizer.title_similarity_factor))
    plt.show()





#plt.plot(title_factor_values, intra_title_avgs, label="Title Intra")
#plt.plot(title_factor_values, intra_abstract_avgs, label="Abstract Intra")
#plt.plot(title_factor_values, inter_title_avgs, label="Title Inter")
#plt.plot(title_factor_values, inter_abstract_avgs, label="Abstract Inter")
#plt.legend()
