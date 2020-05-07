FROM python:3.7-slim-buster

RUN mkdir -p /usr/share/man/man1

RUN apt-get -y update && apt-get install -y --no-install-recommends poppler-utils default-jre \
&& rm -rf /var/lib/apt/lists/*

COPY collabovid-shared/ /collabovid-shared
RUN (cd collabovid-shared; python setup.py sdist) && pip install --no-cache /collabovid-shared/dist/collabovid-shared-0.1.tar.gz && rm -rf /collabovid-shared

ENV PROJECT_DIR=scrape
ENV PROJECT_NAME=scrape

COPY ./${PROJECT_DIR}/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

# Downloads tika server jar
RUN python -c "from tika import tika; tika.checkTikaServer()"

COPY ${PROJECT_DIR} /app
WORKDIR /app
ENV DJANGO_SETTINGS_MODULE=${PROJECT_NAME}.settings

EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["bash"]