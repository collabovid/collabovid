from time import sleep

from django.core.files.uploadedfile import InMemoryUploadedFile

from scrape.src.pdf_extractor import PdfExtractor, PdfExtractError
from scrape.src.static_functions import sanitize_doi
from tasks.definitions import register_task, Runnable

from data.models import Paper


@register_task
class PdfImageDownloader(Runnable):
    @staticmethod
    def task_name():
        return "download-pdf-images"

    def __init__(self, papers=None, *args, **kwargs):
        super(PdfImageDownloader, self).__init__(*args, **kwargs)

        if papers:
            self.papers = papers
        else:
            self.papers = Paper.objects.all()

    def run(self):
        self.log("Download PDF preview images")
        papers = Paper.objects.all()

        for paper in papers:
            if not paper.preview_image and paper.pdf_url:
                self.log(f"Download PDF preview image for {paper.doi}")
                try:
                    sleep(3)
                    pdf_extractor = PdfExtractor(paper.pdf_url)
                    image = pdf_extractor.extract_image()

                    if image:
                        img_name = sanitize_doi(paper.doi) + ".jpg"
                        paper.preview_image.save(img_name, InMemoryUploadedFile(
                            image,  # file
                            None,  # field_name
                            img_name,  # file name
                            'image/jpeg',  # content_type
                            image.tell,  # size
                            None))
                        paper.save()
                except PdfExtractError as ex:
                    self.log(f"Error: {paper.doi}, {ex}")
