from django.http import JsonResponse, HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from src.search.search_engine import get_default_search_engine, SearchEngine
from src.analyze import get_semantic_paper_search, get_similar_paper_finder
import time
import json
from data.models import Paper

from sklearn.cluster import KMeans
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import text


def wait_until(condition, interval=0.1, timeout=10):
    start = time.time()
    while not condition() and time.time() - start < timeout:
        time.sleep(interval)
    return condition()


def important_features(vectorizer, classifier, n=20):
    class_labels = classifier.classes_
    feature_names = vectorizer.get_feature_names()

    for i in range(len(class_labels)):
        topn_class = sorted(zip(classifier.feature_count_[i], feature_names), reverse=True)[:n]

        print("Important words in class", i)

        for coef, feat in topn_class:
            print(class_labels[0], coef, feat)

        print("-----------------------------------------")


def find_topics(request):
    if request.method == "GET":
        semantic_paper_search = get_semantic_paper_search()
        if not wait_until(semantic_paper_search.is_ready):
            return HttpResponseBadRequest("Semantic Paper Search is not initialized yet")
        score_min = float(request.GET.get("score_min", "0"))
        form = json.loads(request.GET.get('form'))
        search_engine = get_default_search_engine()
        search_result = search_engine.search(form, score_min=score_min)

        paper_finder = get_similar_paper_finder()
        if not wait_until(paper_finder.is_ready):
            return HttpResponseBadRequest("Similar Paper finder is not initialized yet")

        ordered_by_score = sorted(search_result.items(), key=lambda x:x[1], reverse=True)[:100]
        ordered_dois, scores = zip(*ordered_by_score)

        ordered_dois = sorted(ordered_dois)

        matrix = paper_finder._vectorizer.extract_paper_matrix(dois=ordered_dois)

        y_pred = KMeans(n_clusters=15).fit_predict(matrix)

        paper_info = list(Paper.objects.filter(pk__in=ordered_dois).values_list('doi', 'title', 'abstract'))

        paper_info = sorted(paper_info, key=lambda x: x[0])

        d, t, a = zip(*paper_info)

        stop_words = text.ENGLISH_STOP_WORDS.union(form['query'].split() +
            ['sars', 'cov', '19', '2019', 'coronavirus', 'covid'] + ['doi', 'preprint', 'pandemic', 'epidemic', 'copyright', 'peer', 'review',
                                                                     'reviewed', 'org', 'https', 'et', 'al', 'author',
                                                                     'figure',
                                                                     'rights', 'reserved', 'permission', 'used',
                                                                     'using', 'biorxiv', 'fig', 'fig.', 'al.',
                                                                     'di', 'la', 'il', 'del', 'le', 'della', 'dei',
                                                                     'delle', 'una', 'da', 'dell', 'non', 'si',
                                                                     'funding', 'covid-19',
                                                                     'covid19', 'sars-cov-2', 'coronavirus', 'method',
                                                                     'study', 'infection', 'public', 'sars', 'datum',
                                                                     'datum',
                                                                     'human', 'peer-reviewed', 'cc-by', 'the(which',
                                                                     'cc-by-nc-nd', 'medrxiv', 'wang',
                                                                     'licenseauthor/funder', 'li',
                                                                     'org/10', 'author/funder', 'available',
                                                                     'licenseit', 'sep2020', 'medrxiv', 'biorxiv', 'pp',
                                                                     'paper',
                                                                     'research', 'license', '2019-ncov', 'i(t', 'grant',
                                                                     'virus', 'health', 'disease', 'infect', 'grant',
                                                                     'show', 'yes', 'ratio', 'size', 'high', 'low',
                                                                     'large', '0(0', 'result', '\\\\r', 'investor',
                                                                     'group', 'allow',
                                                                     'show', 'table', 'plot',
                                                                     'betacov/zhejiang/wz-02/2020',
                                                                     'betacov/zhejiang/hangzhou-', 'david',
                                                                     'betacov/shenzhen/szth-003/2020',
                                                                     'betacov/taiwan/2/2020', 'cov', 'include', 'use',
                                                                     'licensewas', 'whichthis',
                                                                     'vf=0', 'set', 'patient', 'china', 'confirm',
                                                                     'italy', 'novel', 'need', 'pubmed', 'require',
                                                                     'conclusion', 'average',
                                                                     'december', 'february', 'march', 'april',
                                                                     'january'])

        paper_contents = [title + " " + abstract for title, abstract in zip(t, a)]

        word_list = open("vocabs_uncased_spacy.txt").read().splitlines()
        count_vec = CountVectorizer(vocabulary=word_list, stop_words=form['query'].split())
        X_train = count_vec.fit_transform(paper_contents)

        model = MultinomialNB(alpha=0.07)
        model.fit(X_train, y_pred)

        feature_prob = (abs(model.feature_log_prob_))
        labels = count_vec.get_feature_names()
        counts = X_train.toarray().sum(axis=0)
        print(labels)

        important_features(count_vec, model)

        return JsonResponse({'success': True})


def search_similar(request):
    if request.method == "GET":
        score_min = float(request.GET.get("score_min", "0"))
        form = json.loads(request.GET.get('form'))

        filtered, filtered_papers = SearchEngine.filter_papers(form)

        print(form)

        result = dict()

        for doi in filtered_papers.values_list('doi', flat=True):
            result[doi] = 0

        paper_finder = get_similar_paper_finder()
        if not wait_until(paper_finder.is_ready):
            return HttpResponseBadRequest("Similar Paper finder is not initialized yet")

        if form['similar_papers']:
            similar_factor = 1 / len(form['similar_papers'])
            for paper_doi in form['similar_papers']:
                similar_paper = paper_finder.similar(paper_doi)
                for doi, score in similar_paper:
                    if doi in result:
                        result[doi] += score * similar_factor

        if form['different_papers']:
            different_factor = 1 / len(form['different_papers'])
            for paper_doi in form['different_papers']:
                similar_paper = paper_finder.similar(paper_doi)
                for doi, score in similar_paper:
                    if doi in result:
                        result[doi] -= score * different_factor

        # result = {key: val for key, val in result.items() if val > score_min}

        return JsonResponse(result)


def search(request):
    if request.method == "GET":
        semantic_paper_search = get_semantic_paper_search()
        if not wait_until(semantic_paper_search.is_ready):
            return HttpResponseBadRequest("Semantic Paper Search is not initialized yet")

        score_min = float(request.GET.get("score_min", "0"))
        form = json.loads(request.GET.get('form'))
        search_engine = get_default_search_engine()
        search_result = search_engine.search(form, score_min=score_min)

        return JsonResponse(search_result)


def similar(request):
    """
    Api method to retrieve the most similar paper given a doi.
    :param request: Request containing the doi as a HTTP GET parameter
    :return: json response with the list of papers and the corresponding similarity score
    """
    if request.method == "GET":
        paper_finder = get_similar_paper_finder()
        if not wait_until(paper_finder.is_ready):
            return HttpResponseBadRequest("Similar Paper finder is not initialized yet")

        doi = request.GET.get('doi')
        limit = request.GET.get('limit')
        similar_paper = paper_finder.similar(doi, top=limit)
        result = []
        for doi, score in similar_paper:
            result.append({
                'doi': doi,
                'score': score
            })
        return JsonResponse({'similar': result})
    return HttpResponseBadRequest("Only Get is allowed here")


def startup_probe(request):
    paper_finder = get_similar_paper_finder()
    paper_search = get_semantic_paper_search()

    if not paper_finder.is_ready():
        return HttpResponseServerError("Similar Paper finder not ready.")

    if not paper_search.is_ready():
        return HttpResponseServerError("Semantic Paper Search not ready.")

    return HttpResponse("OK")
