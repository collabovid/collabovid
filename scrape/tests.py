from django.test import TestCase

# Create your tests here.
from data.models import Paper, Author
from scrape.scrape_data import get_data

class ScrapeTest(TestCase):
    def test_scrape_data(self):
        get_data(count=5)

        assert len(Paper.objects.all()) == 1
        assert len(Author.objects.all()) == 3

        relations = Paper.objects.all()[0].authors.all()
        assert len(relations) == 3
