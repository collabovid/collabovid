from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models import F


class Topic(models.Model):
    name = models.CharField(default="Unknown", max_length=300)
    description = models.TextField()
    description_html = models.TextField()
    icon_path = models.CharField(max_length=100, default="")

    latent_topic_score = models.BinaryField(null=True)


class PaperHost(models.Model):
    name = models.CharField(max_length=60, unique=True)
    url = models.URLField(null=True, default=None)


class DataSource(models.Model):
    MEDBIORXIV_DATASOURCE_NAME = 'medbiorxiv-updater'
    ARXIV_DATASOURCE_NAME = 'arxiv-updater'

    name = models.CharField(max_length=120, unique=True)

    @property
    def priority(self):
        if self.name == DataSource.MEDBIORXIV_DATASOURCE_NAME:
            return 1
        elif self.name == DataSource.ARXIV_DATASOURCE_NAME:
            return 2
        else:
            return 100


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    citation_count = models.IntegerField(null=True, default=None)
    citations_last_update = models.DateTimeField(null=True, default=None)
    scholar_url = models.URLField(null=True, default=None)
    split_name = models.BooleanField(default=False)  # True iff the name was split by us at the time of creation.
    data_source = models.ForeignKey(DataSource, related_name="authors", on_delete=models.CASCADE, null=True,
                                    default=None)
    class Meta:
        ordering = [F('citation_count').desc(nulls_last=True)]


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
    data_source = models.ForeignKey(DataSource, related_name="papers", on_delete=models.CASCADE, null=True,
                                      default=None)
    version = models.CharField(max_length=40, null=True, default=None)

    data = models.OneToOneField(PaperData, null=True, default=None, related_name='paper', on_delete=models.SET_NULL)

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

    latent_topic_score = models.BinaryField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scrape = models.DateTimeField(null=True, default=None)

    @property
    def percentage_topic_score(self):
        return round(self.topic_score * 100)

    def add_preview_image(self, pillow_image):
        img_name = self.doi.replace("/", "_").replace(".", "_").replace(",", "_").replace(":", "_")
        self.preview_image.save(img_name, InMemoryUploadedFile(pillow_image, None, img_name,
                                                               'image/jpeg', pillow_image.tell, None))
