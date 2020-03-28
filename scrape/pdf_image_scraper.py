from pdf2image import convert_from_bytes
import os
import requests
import django

django.setup()
from data.models import Paper


class PdfImageScraper:
    FOLDER_NAME = "pdf_images"

    def get_image_filename(self, paper: Paper):
        return paper.cleaned_doi + ".jpg"

    def load_images(self, count=None):
        if not os.path.exists(self.FOLDER_NAME):
            os.mkdir(self.FOLDER_NAME)

        all_papers = Paper.objects.all()
        for i, paper in enumerate(all_papers):
            img_filename = os.path.join(self.FOLDER_NAME, paper.image_name)
            if not os.path.isfile(img_filename):

                res = requests.get(paper.pdf_url)
                pages = convert_from_bytes(res.content, first_page=1, last_page=1)
                if len(pages) != 1:
                    print(f"Error creating image for file {i}: {paper.doi}")
                    continue
                pages[0].save(img_filename, 'JPEG')

                print(f"Successfully created image for file {i}: {paper.doi}")
            if count and i >= count:
                break


if __name__ == "__main__":
    scraper = PdfImageScraper()
    scraper.load_images()
