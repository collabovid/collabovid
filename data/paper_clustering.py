import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from yellowbrick.cluster import KElbowVisualizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.cluster import KMeans
from sklearn.preprocessing import FunctionTransformer

import django

django.setup()

from data.models import Paper, Topic


def get_abstract(data):
    return [paper.abstract for paper in data]

def get_title(data):
    return [paper.title for paper in data]

class BasicClustering:

    def ellbow(self, model, X):
        visualizer = KElbowVisualizer(model, k=(20, 21))
        visualizer.fit(X)
        visualizer.show()
        opt_k = visualizer.elbow_value_

        if not opt_k:
            return 3
        print("Optk was ", opt_k)

        return opt_k

    def calculate_clustering(self):
        papers = Paper.objects.all()

        print("Read", papers.count(), "papers")

        X = list(papers)

        abstracts = Pipeline(
            steps=[
                ("get_abstract", FunctionTransformer(get_abstract, validate=False)),
                ("vectorizer", TfidfVectorizer(decode_error='replace', max_df=0.8))
            ])

        #titles = Pipeline(
        #    steps=[
        #        ("get_titles", FunctionTransformer(get_title, validate=False)),
        #        ("vectorizer", TfidfVectorizer(decode_error='replace', max_df=0.8))
        #    ])

        features = FeatureUnion(transformer_list=[("abstracts", abstracts)])

        #kmeans = KMeans()
        #opt_k = self.ellbow(kmeans, features.fit_transform(X))

        kmeans = KMeans(n_clusters=10, n_init=50)

        complete_pipe = Pipeline(steps=[("features", features), ("kmeans", kmeans)])

        predictions = complete_pipe.fit_predict(X)

        for paper, prediction in zip(papers, predictions):
            print(paper.title, prediction)

        return papers, predictions


if __name__ == "__main__":
    clustering = BasicClustering()
    papers, predictions = clustering.calculate_clustering()

    for paper, prediction in zip(papers, predictions):
        topic, created = Topic.objects.get_or_create(pk=prediction)
        paper.topic = topic
        paper.save()
