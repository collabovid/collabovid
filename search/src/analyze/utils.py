import en_core_sci_md
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

nlp = en_core_sci_md.load(disable=["tagger", "parser", "ner"])
nlp.max_length = 2000000

customize_stop_words = [
    'doi', 'preprint', 'copyright', 'peer', 'review', 'reviewed', 'org', 'https', 'et', 'al', 'author', 'figure',
    'rights', 'reserved', 'permission', 'used', 'using', 'biorxiv', 'fig', 'fig.', 'al.',
    'di', 'la', 'il', 'del', 'le', 'della', 'dei', 'delle', 'una', 'da', 'dell', 'non', 'si', 'funding', 'covid-19',
    'covid19', 'sars-cov-2', 'coronavirus', 'method', 'study', 'infection', 'public', 'sars', 'datum', 'datum',
    'human', 'peer-reviewed', 'cc-by', 'the(which', 'cc-by-nc-nd', 'medrxiv', 'wang', 'licenseauthor/funder', 'li',
    'org/10', 'author/funder', 'available', 'licenseit', 'sep2020', 'medrxiv', 'biorxiv', 'pp', 'paper',
    'research', 'license', '2019-ncov', 'i(t', 'grant', 'virus', 'health', 'disease', 'infect', 'grant',
    'show', 'yes', 'ratio', 'size', 'high', 'low', 'large', '0(0', 'result', '\\\\r', 'investor', 'group', 'allow',
    'show', 'table', 'plot', 'betacov/zhejiang/wz-02/2020', 'betacov/zhejiang/hangzhou-', 'david',
    'betacov/shenzhen/szth-003/2020', 'betacov/taiwan/2/2020', 'cov', 'include', 'use', 'licensewas', 'whichthis',
    'vf=0', 'set', 'patient', 'china', 'confirm', 'italy', 'novel', 'need', 'pubmed', 'require', 'conclusion',
    'average',
    'december', 'february', 'march', 'april', 'january', 'pandemic'
]

# Mark them as stop words
for w in customize_stop_words:
    lex = nlp.vocab[w]
    lex.is_stop = True


def spacy_tokenizer(sentence):
    if not sentence:
        return []
    return [word.lemma_ for word in nlp(sentence) if
            not (word.like_num or word.is_stop or word.is_punct or word.is_space or len(
                word) == 1 or (len(word) == 2) or word.text.startswith('doi:'))]


def get_top_n_words(corpus, n=None):
    vec = CountVectorizer(tokenizer=spacy_tokenizer).fit(corpus)
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    return words_freq[:n]


def important_features(vectorizer, classifier, n=20):
    class_labels = classifier.classes_
    feature_names = vectorizer.get_feature_names()
    features_by_class = []
    for _ in range(len(class_labels)):
        features_by_class.append([])
    for i, name in enumerate(feature_names):
        class_idx = np.argmax(classifier.feature_log_prob_[:, i])
        distance_score = (classifier.feature_log_prob_[class_idx, i] - classifier.feature_log_prob_[:, i]).sum()
        features_by_class[class_idx].append((name, distance_score))

    for i in range(len(class_labels)):
        features_by_class[i] = [x[0] for x in sorted(features_by_class[i], key=lambda x: x[1], reverse=True)[:n]]
    return features_by_class


def get_predictive_words(contents_list, top=10):
    all_contents = []
    for contents in contents_list:
        all_contents += contents

    y = []
    for i, contents in enumerate(contents_list):
        y += [i] * len(contents)
    y = np.array(y)

    count_vec = CountVectorizer(tokenizer=spacy_tokenizer, token_pattern=None)
    X_train = count_vec.fit_transform(all_contents)

    model = MultinomialNB(alpha=0.07)
    model.fit(X_train, y)

    feature_prob = (abs(model.feature_log_prob_))
    return important_features(count_vec, model, n=top)
