from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Author, Journal, Paper

from elasticsearch_dsl import analyzer
from elasticsearch_dsl.analysis import token_filter


edge_ngram_completion_filter = token_filter(
    'edge_ngram_completion_filter',
    type="edge_ngram",
    min_gram=1,
    max_gram=20
)

edge_ngram_completion = analyzer(
    "edge_ngram_completion",
    tokenizer="standard",
    filter=["lowercase", edge_ngram_completion_filter]
)


@registry.register_document
class PaperDocument(Document):
    class Index:
        name = 'papers'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0,
                    'max_result_window': 100000}

    authors = fields.ObjectField(properties={
        'pk': fields.IntegerField(),
        'full_name': fields.TextField(),
    })

    journal = fields.ObjectField(properties={
        'pk': fields.IntegerField(),
    })

    categories = fields.ObjectField(properties={
        'pk': fields.IntegerField(),
    })

    class Django:
        model = Paper
        fields = [
            'title',
            'abstract',
            'published_at',
            'is_preprint',
        ]


@registry.register_document
class AuthorDocument(Document):
    class Index:
        name = 'authors'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    full_name_suggest = fields.CompletionField(attr='full_name_suggest')

    class Django:
        model = Author
        fields = [
            'first_name',
            'last_name',
        ]


@registry.register_document
class JournalDocument(Document):
    class Index:
        name = 'journals'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    name_suggest = fields.CompletionField(attr='name', analyzer=edge_ngram_completion)

    class Django:
        model = Journal

