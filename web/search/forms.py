from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder

from search.tagify.tagify_searchable import *
from django.conf import settings


class MinLengthValidator(validators.MinLengthValidator):
    message = 'Ensure this value has at least %(limit_value)d elements (it has %(show_value)d).'


class MaxLengthValidator(validators.MaxLengthValidator):
    message = 'Ensure this value has at most %(limit_value)d elements (it has %(show_value)d).'


class CommaSeparatedCharField(forms.Field):
    """
    The comma separated char field is used for our lists so that the url looks nicer
    """

    def __init__(self, dedup=True, max_length=None, min_length=None, *args, **kwargs):
        self.dedup, self.max_length, self.min_length = dedup, max_length, min_length
        super(CommaSeparatedCharField, self).__init__(*args, **kwargs)
        if min_length is not None:
            self.validators.append(MinLengthValidator(min_length))
        if max_length is not None:
            self.validators.append(MaxLengthValidator(max_length))

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return []

        value = [item.strip() for item in value.split(',') if item.strip()]
        if self.dedup:
            value = list(set(value))

        return value

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value


class CommaSeparatedIntegerField(forms.Field):
    default_error_messages = {
        'invalid': 'Enter comma separated numbers only.',
    }

    def __init__(self, dedup=True, max_length=None, min_length=None, *args, **kwargs):
        self.dedup, self.max_length, self.min_length = dedup, max_length, min_length
        super(CommaSeparatedIntegerField, self).__init__(*args, **kwargs)
        if min_length is not None:
            self.validators.append(MinLengthValidator(min_length))
        if max_length is not None:
            self.validators.append(MaxLengthValidator(max_length))

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return []

        try:
            value = [int(item.strip()) for item in value.split(',') if item.strip()]
            if self.dedup:
                value = list(set(value))
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid'])

        return value

    def clean(self, value):
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value


class SearchForm(forms.Form):
    TAB_CHOICES = [('combined', 'Semantic Search'), ('keyword', 'Keyword Search')]
    SORT_CHOICES = [('top', 'Relevance'), ('newest', 'Newest')]

    AUTHOR_CONNECTION_CHOICES = [('one', 'One matching'), ('all', 'All matching')]
    ARTICLE_TYPES = [('all', 'All'), ('reviewed', 'Reviewed'), ('preprints', 'Preprints')]

    RESULT_TYPE_PAPERS = 'papers'
    RESULT_TYPE_STATISTICS = 'statistics'

    RESULT_TYPES = [(RESULT_TYPE_PAPERS, 'Papers'), (RESULT_TYPE_STATISTICS, 'Statistics')]

    query = forms.CharField(required=False, initial='')
    tab = forms.ChoiceField(choices=TAB_CHOICES, required=True)
    sorted_by = forms.ChoiceField(choices=SORT_CHOICES, required=True)

    authors_connection = forms.ChoiceField(choices=AUTHOR_CONNECTION_CHOICES, required=False)
    article_type = forms.ChoiceField(choices=ARTICLE_TYPES, required=False)

    result_type = forms.ChoiceField(choices=RESULT_TYPES, required=True)

    authors = CommaSeparatedIntegerField(required=False)
    journals = CommaSeparatedIntegerField(required=False)
    locations = CommaSeparatedIntegerField(required=False)

    categories = CommaSeparatedIntegerField(required=False)

    published_at_start = forms.DateField(required=False)
    published_at_end = forms.DateField(required=False)

    page = forms.IntegerField(required=False)

    defaults = {
        'tab': 'combined',
        'article_type': 'all',
        'authors_connection': 'one',
        'sorted_by': 'top',
        'result_type': 'papers',
    }

    def __init__(self, data, *args, **kwargs):
        """
        By default Django does not allow bounded forms to have default values. We set the default values when no values
        are set, i.e. when creating the form with request.GET and e.g. 'top' key is missing.
        :param data:
        :param args:
        :param kwargs:
        """
        super(SearchForm, self).__init__(data, *args, **kwargs)
        self.data = self.defaults.copy()
        for key, val in data.items():
            if not data.get(key):
                continue
            field = self.fields.get(key)
            if field and getattr(field.widget, 'allow_multiple_selected', False):
                self.data[key] = data.getlist(key)
            else:
                self.data[key] = data.get(key)

    def to_dict(self):
        return {'published_at_start': self.cleaned_data['published_at_start'],
                'published_at_end': self.cleaned_data['published_at_end'],
                'query': self.cleaned_data['query'],
                'tab': self.cleaned_data['tab'],
                'sorted_by': self.cleaned_data['sorted_by'],
                'authors': self.cleaned_data['authors'],
                'authors_connection': self.cleaned_data['authors_connection'],
                'categories': self.cleaned_data['categories'],
                'article_type': self.cleaned_data['article_type'],
                'journals': self.cleaned_data['journals'],
                'locations': self.cleaned_data['locations'],
                'result_type': self.cleaned_data['result_type'],
                'page': self.cleaned_data['page']}

    def to_json(self):
        """
        The json format is used to transfer the filled-out form object to search
        :return:
        """

        return json.dumps(self.to_dict(), cls=DjangoJSONEncoder)

    @property
    def interesting(self):
        return self.cleaned_data['query'].strip() or self.cleaned_data['authors'] or self.cleaned_data['categories'] or \
               self.cleaned_data['journals'] or self.cleaned_data['locations'] or self.cleaned_data[
                   'published_at_start'] or self.cleaned_data['published_at_end']

    @property
    def url(self):
        return settings.SEARCH_SERVICE_URL + "/search"
