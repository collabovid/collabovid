from pdf2image import convert_from_bytes
import os
import requests

from data.models import Paper
from django.conf import settings

class PdfImageScraper:

    def load_images(self, count=None):
        if not os.path.exists(settings.PDF_IMAGE_FOLDER):
            os.mkdir(settings.PDF_IMAGE_FOLDER)

        all_papers = Paper.objects.all()
        for i, paper in enumerate(all_papers):
            if not os.path.isfile(paper.image_path):
                res = requests.get(paper.pdf_url)
                pages = convert_from_bytes(res.content, first_page=1, last_page=1)
                if len(pages) != 1:
                    print(f"Error creating image for file {i}: {paper.doi}")
                    continue
                pages[0].save(paper.image_path, 'JPEG')

                print(f"Successfully created image for file {i}: {paper.doi}")
            if count and i - 1 >= count:
                break
