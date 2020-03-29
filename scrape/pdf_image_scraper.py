from pdf2image import convert_from_bytes
import os
import requests

from data.models import Paper
from django.conf import settings

from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile

class PdfImageScraper:

    def cleaned_doi(self, paper):
        return paper.doi.replace("/", "").replace(".", "")

    def load_images(self):
        all_papers = Paper.objects.all()
        for i, paper in enumerate(all_papers):
            if not paper.preview_image:
                res = requests.get(paper.pdf_url)
                pages = convert_from_bytes(res.content, first_page=1, last_page=1)
                if len(pages) != 1:
                    print(f"Error creating image for file {i}: {paper.doi}")
                    continue

                buffer = BytesIO()
                pages[0].save(fp=buffer, format='JPEG')

                pillow_image = ContentFile(buffer.getvalue())

                img_name = self.cleaned_doi(paper) + ".jpg"
                paper.preview_image.save(img_name, InMemoryUploadedFile(
                    pillow_image,  # file
                    None,  # field_name
                    img_name,  # file name
                    'image/jpeg',  # content_type
                    pillow_image.tell,  # size
                    None))

                paper.save()

                print(f"Successfully created image for file {i}: {paper.doi}")
