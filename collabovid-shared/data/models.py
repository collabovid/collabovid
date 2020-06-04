from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
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
            return 10
        else:
            return 100

    @property
    def check_covid_related(self):
        if self.value == DataSource.MEDBIORXIV:
            return False
        else:
            return True


class Journal(models.Model):
    name = models.CharField(max_length=200, unique=True)
    alias = models.CharField(max_length=200, null=True, default=None, blank=True)
    url = models.URLField(null=True, default=None, blank=True)

    @property
    def displayname(self):
        return self.alias if self.alias else self.name

    @staticmethod
    def max_length(field: str):
        return Journal._meta.get_field(field).max_length


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    @staticmethod
    def max_length(field: str):
        return Author._meta.get_field(field).max_length


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
    topic_score = models.FloatField(default=0.0)
    abstract = models.TextField()

    url = models.URLField(null=True, default=None)
    pdf_url = models.URLField(null=True, default=None)
    is_preprint = models.BooleanField(default=True)

    published_at = models.DateField(null=True, default=None)
    journal = models.ForeignKey(Journal, related_name="papers", on_delete=models.CASCADE, null=True, default=None)

    latent_topic_score = models.BinaryField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scrape = models.DateTimeField(null=True, default=None)

    @property
    def percentage_topic_score(self):
        return round(self.topic_score * 100)

    def add_preview_image(self, pillow_image):
        img_name = self.doi.replace('/', '_').replace('.', '_').replace(',', '_').replace(':', '_') + '.jpg'
        self.preview_image.save(img_name, InMemoryUploadedFile(pillow_image, None, img_name,
                                                               'image/jpeg', pillow_image.tell, None))

    @staticmethod
    def max_length(field: str):
        return Paper._meta.get_field(field).max_length
