from tika import parser
import requests
from data.models import Paper, PaperData
from tqdm import tqdm

class PdfContentScraper:

    def load_contents(self):
        all_papers = list(Paper.objects.all())
        for i, paper in enumerate(tqdm(all_papers)):
            if not paper.data or not paper.data.content:
                res = requests.get(paper.pdf_url)
                self.parse_response(paper, res)

    def parse_response(self, paper, response):

        if paper.data and paper.data.content:
            return

        # Extract text from document
        content = parser.from_buffer(response.content)
        if 'content' in content:
            text = content['content']
        else:
            return
        # Convert to string
        text = str(text)
        # Ensure text is utf-8 formatted
        safe_text = text.encode('utf-8', errors='ignore')
        # Escape any \ issues
        safe_text = str(safe_text).replace('\\', '\\\\').replace('"', '\\"')

        if not paper.data:
            paper.data = PaperData(content=safe_text)
        else:
            paper.data.content = safe_text

        paper.data.save()
        paper.save()


