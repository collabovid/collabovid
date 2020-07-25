from django import forms
from django.forms import Form, ModelForm

from data.models import Paper, Journal


class PaperForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PaperForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'edit-field'

    class Meta:
        model = Paper
        fields = ['title', 'abstract', 'is_preprint',
                  'version', 'pubmed_id', 'published_at', 'url', 'pdf_url',]
        widgets = {
            'published_at': forms.DateInput(format='%Y-%m-%d',
                                            attrs={'class': 'form-control', 'type': 'date'})}