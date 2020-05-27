import requests
import re

from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from tika import parser


class PdfExtractError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.msg


class PdfExtractor:
    def __init__(self, pdf_url):
        self._pdf_response = None
        self._pdf_url = pdf_url

    def _load_pdf_response(self):
        if not self._pdf_response:
            try:
                self._pdf_response = requests.get(self._pdf_url)
            except requests.exceptions.RequestException as ex:
                raise PdfExtractError(f"Coud not download PDF file: {ex}")
            if self._pdf_response.status_code != 200:
                raise PdfExtractError(f"Invalid HTTP status code: {self._pdf_response.status_code}")
            if self._pdf_response.headers['Content-Type'] != 'application/pdf':
                raise PdfExtractError(f"HTTP content type is {self._pdf_response.headers['Content-Type']}. Expect "
                                      f"application/pdf")

    def extract_contents(self):
        """
        Extracts the content of the PDF file.
        :return: The content of the PDF file as string, or None if impossible.
        """
        self._load_pdf_response()

        if not self._pdf_response or self._pdf_response.status_code != 200:
            print(f'No response for pdf url: {self._pdf_url}')
            return None

        content = parser.from_buffer(self._pdf_response.content)
        if 'content' in content:
            text = content['content']
        else:
            return None

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

        return safe_text

    def extract_image(self, page=1):
        """
        Extracts the preview image from the PDF.
        :param page: Sets, which PDF page should appear on the preview. Interesting for Kaggle dataset,
                     where the first page often/always (?) is a disclaimer.
        :return: The preview image as ContentFile or None, if an error occurs.
        """
        self._load_pdf_response()

        if not self._pdf_response or self._pdf_response.status_code != 200:
            print(f'Problem with response in extracting image from {self._pdf_url}')
            return None
        try:
            pages = convert_from_bytes(self._pdf_response.content, first_page=page, last_page=page)
        except (PDFPageCountError, PDFSyntaxError):
            return None

        if len(pages) != 1:
            return None

        buffer = BytesIO()
        pages[0].thumbnail((400, 400), Image.ANTIALIAS)
        pages[0].save(fp=buffer, format='JPEG')

        pillow_image = ContentFile(buffer.getvalue())
        return pillow_image
