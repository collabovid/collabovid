# Note: Run this script from the top level directory (covid19-publications)

import os
import requests
import shutil

from zipfile import ZipFile


if __name__ == "__main__":
    DOWNLOAD_URL = 'https://dl.dropboxusercontent.com/s/ypzbzlb60b8acmc/pdf_images.zip'

    IMAGES_FOLDER = 'pdf_images'

    TMP_DIR = 'tmp'
    TMP_FILENAME = 'images.zip'

    FILE_PATH = os.path.join(TMP_DIR, TMP_FILENAME)
    EXTRACTED_FOLDER_PATH = os.path.join(TMP_DIR, IMAGES_FOLDER)

    if os.path.isdir(os.path.join("static", IMAGES_FOLDER)):
        print(f'Image Folder already present, ending..', os.path.join("static", IMAGES_FOLDER))
        exit(0)

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

    print(f'Moving {EXTRACTED_FOLDER_PATH} to {IMAGES_FOLDER}')

    shutil.move(EXTRACTED_FOLDER_PATH, os.path.join("static", IMAGES_FOLDER))

    print(f'Cleaning up: Removing temp directory {TMP_DIR}')
    shutil.rmtree(TMP_DIR)