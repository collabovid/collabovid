from django import forms
from django.forms import ModelForm

from data.models import Paper, PaperData


class EditForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'edit-field'


class PaperForm(EditForm):
    def __init__(self, *args, **kwargs):
        super(PaperForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Paper
        fields = ['title', 'is_preprint',
                  'version', 'pubmed_id', 'published_at', 'url', 'pdf_url']
        widgets = {
            'published_at': forms.DateInput(format='%Y-%m-%d',
                                            attrs={'class': 'form-control', 'type': 'date'})}


class PaperDataForm(EditForm):
    def __init__(self, *args, **kwargs):
        super(PaperDataForm, self).__init__(*args, **kwargs)

    class Meta:
        model = PaperData
        fields = ['abstract']
