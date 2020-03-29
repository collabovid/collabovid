# Note: Run this script from the top level directory (covid19-publications)

import os
import requests
import shutil


from zipfile import ZipFile
from PIL import Image
import django

django.setup()

from data.models import Paper
from django.db.models import Q

from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile

def cleaned_doi(paper):
    return paper.doi.replace("/", "").replace(".", "")


if __name__ == "__main__":

    print(Paper.objects.filter(~Q(preview_image__exact='')).count())

    if Paper.objects.filter(~Q(preview_image__exact='')).count() == 0:
        DOWNLOAD_URL = 'https://dl.dropboxusercontent.com/s/ypzbzlb60b8acmc/pdf_images.zip'

        IMAGES_FOLDER = 'pdf_images'

        TMP_DIR = 'tmp'
        TMP_FILENAME = 'images.zip'

        FILE_PATH = os.path.join(TMP_DIR, TMP_FILENAME)
        EXTRACTED_FOLDER_PATH = os.path.join(TMP_DIR, IMAGES_FOLDER)

        if not os.path.isdir(TMP_DIR):
            print('Creating tmp directory')
            os.mkdir(TMP_DIR)

        print('Downloading zip file.')
        r = requests.get(DOWNLOAD_URL)

        with open(FILE_PATH, 'wb') as f:
            f.write(r.content)
        print('Download complete. Extracting..')

        with ZipFile(FILE_PATH, 'r') as z:
            z.extractall(path=TMP_DIR)

        for paper in Paper.objects.all():

            image = Image.open(os.path.join(EXTRACTED_FOLDER_PATH, cleaned_doi(paper) + ".jpg"))

            buffer = BytesIO()
            image.save(fp=buffer, format='JPEG')

            pillow_image = ContentFile(buffer.getvalue())

            img_name = cleaned_doi(paper) + ".jpg"
            paper.preview_image.save(img_name, InMemoryUploadedFile(
                pillow_image,  # file
                None,  # field_name
                img_name,  # file name
                'image/jpeg',  # content_type
                pillow_image.tell,  # size
                None))

            paper.save()

        shutil.rmtree(TMP_DIR)
