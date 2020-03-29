import os
import requests
import shutil

from django.conf import settings
from zipfile import ZipFile


class ImageDownloader:
    DOWNLOAD_URL = 'https://dl.dropboxusercontent.com/s/ypzbzlb60b8acmc/pdf_images.zip'

    IMAGES_FOLDER = 'pdf_images'

    TMP_DIR = 'tmp'
    TMP_FILENAME = 'images.zip'

    FILE_PATH = os.path.join(TMP_DIR, TMP_FILENAME)
    EXTRACTED_FOLDER_PATH = os.path.join(TMP_DIR, IMAGES_FOLDER)

    def download_images(self):
        if os.path.isdir(settings.PDF_IMAGE_FOLDER):
            print(f'Removing current image folder {settings.PDF_IMAGE_FOLDER}')
            shutil.rmtree(settings.PDF_IMAGE_FOLDER)

        if not os.path.isdir("tmp"):
            print('Creating tmp directory')
            os.mkdir('tmp')

        print('Downloading zip file.')
        r = requests.get(self.DOWNLOAD_URL)

        with open(self.FILE_PATH, 'wb') as f:
            f.write(r.content)
        print('Download complete. Extracting..')

        with ZipFile(self.FILE_PATH, 'r') as z:
            z.extractall(path=self.TMP_DIR)

        print(f'Moving {self.EXTRACTED_FOLDER_PATH} to {settings.BASE_DIR}')
        shutil.move(self.EXTRACTED_FOLDER_PATH, settings.BASE_DIR)
        print(f'Cleaning up: Removing temp directory {self.TMP_DIR}')
        shutil.rmtree(self.TMP_DIR)
