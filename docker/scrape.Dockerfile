FROM python:3.7-slim-buster

RUN mkdir -p /usr/share/man/man1

RUN apt-get -y update && apt-get install -y --no-install-recommends poppler-utils default-jre git \
&& rm -rf /var/lib/apt/lists/*

ENV PROJECT_DIR=scrape
ENV PROJECT_NAME=scrape

RUN pip install --no-cache requests==2.23.0

COPY ./${PROJECT_DIR}/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

ENV TIKA_STARTUP_MAX_RETRY=10

# Downloads tika server jar
RUN python -c "from tika import tika; tika.checkTikaServer()"

COPY collabovid-shared/dist /collabovid-shared/dist
RUN pip install --no-cache /collabovid-shared/dist/*.whl && rm -rf /collabovid-shared

COPY ./collabovid-store/dist /collabovid-store
RUN pip install --no-cache /collabovid-store/*.whl

COPY ${PROJECT_DIR} /app
WORKDIR /app

EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["bash"]