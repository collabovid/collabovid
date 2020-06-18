from time import sleep

from data.models import DataSource, Paper
from src.pdf_extractor import PdfExtractError, PdfFromUrlExtractor
from src.updater.elsevier_update import ElsevierUpdater
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

        for paper in self.progress(Paper.objects.filter(preview_image__in=['', None])):
            if paper.data_source_value == DataSource.ELSEVIER:
                self.log(f"Download PDF preview image for {paper.doi}")
                ElsevierUpdater.update_pdf_data(paper, extract_image=True, extract_content=False)
                paper.save()
            else:
                if paper.pdf_url:
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
