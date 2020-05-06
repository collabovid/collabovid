import requests
import re
import gc

from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from tika import parser

from multiprocessing.pool import ThreadPool

_POOL_SIZE = 16


class PdfDownloadError(Exception):
    @property
    def msg(self):
        return "Could not download PDF"


def get_and_except(url):
    try:
        return requests.get(url)
    except requests.exceptions.RequestException as ex:
        print(ex)
        return None


class PdfExtractor:
    def __init__(self, pdf_urls):
        gc.collect()
        self._pdf_responses = None
        self._pdf_urls = pdf_urls

    def _load_pdf_responses(self):
        if not self._pdf_responses:
            pool = ThreadPool(_POOL_SIZE)
            self._pdf_responses = pool.map(get_and_except, self._pdf_urls)
            pool.close()
            pool.join()

    def extract_contents(self):
        """
        Extracts the content of the PDF file.
        :return: The content of the PDF file as string, or None if impossible.
        """
        self._load_pdf_responses()

        contents = []
        for i, response in enumerate(self._pdf_responses):
            if not response or response.status_code != 200:
                print(f'No response for pdf url: {self._pdf_urls[i]}')
                contents.append(None)
                continue

            content = parser.from_buffer(response.content)
            if 'content' in content:
                text = content['content']
            else:
                contents.append(None)
                continue

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
            contents.append(safe_text)

        return contents

    def extract_images(self, page=1):
        """
        Extracts the preview image from the PDF.
        :param page: Sets, which PDF page should appear on the preview. Interesting for Kaggle dataset,
                     where the first page often/always (?) is a disclaimer.
        :return: The preview image as ContentFile or None, if an error occurs.
        """
        self._load_pdf_responses()

        images = []
        for i, response in enumerate(self._pdf_responses):
            if not response or response.status_code != 200:
                print(f'Problem with response in extracting image from {self._pdf_urls[i]}')
                images.append(None)
                continue
            try:
                pages = convert_from_bytes(response.content, first_page=page, last_page=page)
            except (PDFPageCountError, PDFSyntaxError):
                images.append(None)
                continue

            if len(pages) != 1:
                images.append(None)
                continue

            buffer = BytesIO()
            pages[0].thumbnail((400, 400), Image.ANTIALIAS)
            pages[0].save(fp=buffer, format='JPEG')

            pillow_image = ContentFile(buffer.getvalue())
            images.append(pillow_image)

        return images
