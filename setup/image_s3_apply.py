import django

django.setup()

from data.models import Paper
from django.db.models import Q

def cleaned_doi(paper):
    return paper.doi.replace("/", "").replace(".", "")

if __name__ == "__main__":

    if Paper.objects.filter(~Q(preview_image__exact='')).count() == 0:

        for paper in Paper.objects.all():
            paper.preview_image = "pdf_images/"+cleaned_doi(paper)+".jpg"
            paper.save()

        print("Successfully changed all image paths.")