from pdf2image import convert_from_bytes
import requests

from PIL import Image

from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from tasks import register_task, Runnable


@register_task
class PdfImageScraper(Runnable):

    @staticmethod
    def task_name():
        return "scrape-pdf-image"

    def __init__(self, papers, *args, **kwargs):
        super(PdfImageScraper, self).__init__(*args, **kwargs)
        self.papers = papers

    def run(self):
        skipped_papers = 0
        for i, paper in enumerate(self.papers):
            if not paper.preview_image:
                res = requests.get(paper.pdf_url)
                self.load_image_from_pdf_response(paper, res)
            else:
                skipped_papers += 1

        self.log("Skipped", skipped_papers)

    @staticmethod
    def cleaned_doi(paper):
        return paper.doi.replace("/", "").replace(".", "")

    @staticmethod
    def load_image_from_pdf_response(paper, response):
        pages = convert_from_bytes(response.content, first_page=1, last_page=1)
        if len(pages) != 1:
            print(f"Error creating image for file: {paper.doi}")
            return

        buffer = BytesIO()
        pages[0].thumbnail((400,400), Image.ANTIALIAS)
        pages[0].save(fp=buffer, format='JPEG')

        pillow_image = ContentFile(buffer.getvalue())

        img_name = PdfImageScraper.cleaned_doi(paper) + ".jpg"
        paper.preview_image.save(img_name, InMemoryUploadedFile(
            pillow_image,  # file
            None,  # field_name
            img_name,  # file name
            'image/jpeg',  # content_type
            pillow_image.tell,  # size
            None))

        paper.save()

        print(f"Successfully created image for: {paper.doi}")
