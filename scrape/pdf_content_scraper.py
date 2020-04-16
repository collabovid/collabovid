from tika import parser
import requests
from data.models import Paper, PaperData
import re

from tasks import Runnable, register_task


@register_task
class PdfContentScraper(Runnable):

    @staticmethod
    def task_name():
        return "scrape-pdf-content"

    def __init__(self, papers = None, *args, **kwargs):
        super(PdfContentScraper, self).__init__(*args, **kwargs)

        if papers:
            self.papers = papers
        else:
            self.papers = Paper.objects.all()

    def run(self):
        skipped_papers = 0
        for i, paper in enumerate(self.papers):
            if not paper.data or not paper.data.content:
                self.log("Scraping content of", paper.doi)
                res = requests.get(paper.pdf_url)
                PdfContentScraper.parse_response(self, paper, res)
                self.log("Got content of", paper.doi, "with length", len(paper.data.content))
            else:
                skipped_papers += 1

        self.log("Skipped", skipped_papers)

    @staticmethod
    def parse_response(runnable: Runnable, paper, response):
        """
        Todo: this methods does some unnecessary conversion.
        :param paper:
        :param response:
        :return:
        """

        if paper.data and paper.data.content:
            return

        # Extract text from document
        content = parser.from_buffer(response.content)
        if 'content' in content:
            text = content['content']
        else:
            runnable.log("No Content found for", paper.doi)
            return

        # Convert to string
        text = str(text)
        # Ensure text is utf-8 formatted
        safe_text = text.encode('utf-8', errors='ignore')
        # Escape any \ issues
        safe_text = str(safe_text).replace('\\', '\\\\').replace('"', '\\"')

        safe_text = safe_text[2:-1]

        safe_text = safe_text.replace('author/funder. All rights reserved. No reuse allowed without permission.',
                                      '')
        safe_text = safe_text.replace('(which was not peer-reviewed) is the', '')
        safe_text = safe_text.replace('bioRxiv preprint', '')

        safe_text = safe_text.replace('. CC-BY-NC-ND 4.0 International license', '')
        safe_text = safe_text.replace('It is made available under a', '')
        safe_text = safe_text.replace(
            'is the author/funder, who has granted medRxiv a license to display the preprint in perpetuity.', '')
        safe_text = safe_text.replace('(which was not peer-reviewed)', '')
        safe_text = safe_text.replace('The copyright holder for this preprint', '')
        safe_text = safe_text.replace('medRxiv preprint', '')

        #  if enabled, try to remove everything after "References" line
        # match = re.match(r"(.*)\\\\n\s*(R|r)eferences:?\s*\\\\n")
        # if match:
        #     safe_text = match.group(1)

        safe_text = re.sub(r"\\\\t|\\\\n|\\\\x\S\S", ' ', safe_text)
        safe_text = re.sub(r"http[^\s\\]*", '', safe_text)
        safe_text = re.sub(r"[\w\.-]+@[\w\.-]+(\.[\w]+)+", '', safe_text)  # remove e-mail adresses
        safe_text = re.sub(r"\.", '. ', safe_text)
        safe_text = re.sub(r"\s+", ' ', safe_text)
        safe_text = re.sub(r"\[\d+\]", '', safe_text)  # Delete all references like [12])

        if not paper.data:
            paper.data = PaperData(content=safe_text)
        else:
            paper.data.content = safe_text

        paper.data.save()
        paper.save()
