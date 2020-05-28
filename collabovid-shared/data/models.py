from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy


class Topic(models.Model):
    name = models.CharField(default="Unknown", max_length=300)
    description = models.TextField()
    description_html = models.TextField()
    icon_path = models.CharField(max_length=100, default="")

    latent_topic_score = models.BinaryField(null=True)


class PaperHost(models.Model):
    name = models.CharField(max_length=60, unique=True)
    url = models.URLField(null=True, default=None)


class DataSource(models.IntegerChoices):
    MEDBIORXIV = 0, gettext_lazy('medbioRxiv')
    ARXIV = 1, gettext_lazy('arXiv')
    PUBMED = 2, gettext_lazy('pubmed')

    @property
    def priority(self):
        if self.value == DataSource.MEDBIORXIV:
            return 0
        if self.value == DataSource.ARXIV:
            return 1
        elif self.value == DataSource.PUBMED:
            return 0
        else:
            return 100


class Journal(models.Model):
    name = models.CharField(max_length=200, unique=True)


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)


class Category(models.Model):
    """
    e.g. Microbiology
    """
    name = models.CharField(max_length=200, primary_key=True)


class PaperData(models.Model):
    """
    Model to store large data which should not be loaded on each select on a regular Paper
    """
    content = models.TextField(null=True, default=None)


class PaperState(models.IntegerChoices):
    BULLSHIT = 0, gettext_lazy('Declined')  # Manually decided to not use this record
    UNKNOWN = 2, gettext_lazy('Unknown')  # Automatic check not executed or returned False
    AUTOMATICALLY_ACCEPTED = 3, gettext_lazy('Automatically accepted')  # Automatic check returned True
    VERIFIED = 4, gettext_lazy('Verified')  # Manually verified


class Paper(models.Model):
    SORTED_BY_TOPIC_SCORE = 1
    SORTED_BY_NEWEST = 2
    SORTED_BY_SCORE = 3

    preview_image = models.ImageField(upload_to="pdf_images", null=True, default=None)

    doi = models.CharField(max_length=100, primary_key=True)

    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, related_name="publications")
    category = models.ForeignKey(Category, related_name="papers", on_delete=models.CASCADE, null=True, default=None)
    host = models.ForeignKey(PaperHost, related_name="papers", on_delete=models.CASCADE)
    data_source_value = models.IntegerField(choices=DataSource.choices, null=True)
    version = models.CharField(max_length=40, null=True, default=None)

    data = models.OneToOneField(PaperData, null=True, default=None, related_name='paper', on_delete=models.SET_NULL)

    pubmed_id = models.CharField(max_length=20, unique=True, null=True, default=None)

    topic = models.ForeignKey(Topic,
                              related_name="papers",
                              null=True,
                              default=None,
                              on_delete=models.SET_DEFAULT)
    covid_related = models.BooleanField(null=True, default=None)
    paper_state = models.IntegerField(choices=PaperState.choices, default=PaperState.UNKNOWN)
    topic_score = models.FloatField(default=0.0)
    abstract = models.TextField(null=True)

    url = models.URLField(null=True, default=None)
    pdf_url = models.URLField(null=True, default=None)
    is_preprint = models.BooleanField(default=True)

    published_at = models.DateField(null=True, default=None)
    journal = models.ForeignKey(Journal, related_name="papers", on_delete=models.CASCADE, null=True, default=None)

    latent_topic_score = models.BinaryField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scrape = models.DateTimeField(null=True, default=None)

    def automatic_state_check(self, save=False):
        if self.paper_state in (PaperState.UNKNOWN, PaperState.AUTOMATICALLY_ACCEPTED):
            success = len(self.title.split()) > 4 and self.abstract and len(self.abstract.split()) >= 20
            self.paper_state = PaperState.AUTOMATICALLY_ACCEPTED if success else PaperState.UNKNOWN
            if save:
                self.save()

    @property
    def visible(self):
        return ((self.covid_related or self.data_source_value and DataSource(
            self.data_source_value).name == DataSource.MEDBIORXIV.name)
                and self.paper_state in (PaperState.AUTOMATICALLY_ACCEPTED, PaperState.VERIFIED))

    @staticmethod
    def get_visible_papers():
        paper_query = (Q(covid_related=True) | Q(data_source_value=DataSource.MEDBIORXIV.value)) & Q(
            paper_state__in=[PaperState.AUTOMATICALLY_ACCEPTED, PaperState.VERIFIED]
        )
        return Paper.objects.filter(paper_query)

    @property
    def percentage_topic_score(self):
        return round(self.topic_score * 100)

    def add_preview_image(self, pillow_image):
        img_name = self.doi.replace('/', '_').replace('.', '_').replace(',', '_').replace(':', '_') + '.jpg'
        self.preview_image.save(img_name, InMemoryUploadedFile(pillow_image, None, img_name,
                                                               'image/jpeg', pillow_image.tell, None))
