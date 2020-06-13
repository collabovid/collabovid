from time import sleep

from data.models import Paper
from src.pdf_extractor import PdfExtractError, PdfFromUrlExtractor
from tasks.definitions import register_task, Runnable


@register_task
class PdfImageDownloadTask(Runnable):
    @staticmethod
    def task_name():
        return "download-pdf-images"

    def __init__(self, papers=None, *args, **kwargs):
        super(PdfImageDownloadTask, self).__init__(*args, **kwargs)

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
                    pdf_extractor = PdfFromUrlExtractor(paper.pdf_url)
                    image = pdf_extractor.extract_image()

                    if image:
                        paper.add_preview_image(image)
                        paper.save()
                except PdfExtractError as ex:
                    self.log(f"Error: {paper.doi}, {ex}")
