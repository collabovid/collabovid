def cleaned_doi(paper):
    return paper.doi.replace("/", "").replace(".", "")

def run(output):
    from data.models import Paper
    from django.db.models import Q

    if Paper.objects.filter(~Q(preview_image__exact='')).count() == 0:

        for paper in Paper.objects.all():
            paper.preview_image = "pdf_images/"+cleaned_doi(paper)+".jpg"
            paper.save()

        output("Successfully changed all image paths.")

    output("Some papers have images. Skipping...")


if __name__ == "__main__":
    import django
    django.setup()

    run(print)
