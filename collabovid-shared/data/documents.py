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
class AuthorDocument(Document):
    class Index:
        name = 'authors'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    full_name_suggest = fields.CompletionField(attr='full_name_suggest')
    full_name = fields.TextField(attr='full_name')

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

    title = fields.TextField(analyzer='english')
    abstract = fields.TextField(analyzer='english')

    class Django:
        model = Paper

        related_models = [Author]

    def get_instances_from_related(self, related_instance):
        """If related_models is set, define how to retrieve the paper instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, Author):
            return related_instance.publications.all()
