FROM collabovid-base:latest

ENV PROJECT_DIR=web
ENV PROJECT_NAME=web

COPY ./${PROJECT_DIR}/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

COPY collabovid-shared/ /collabovid-shared
RUN (cd collabovid-shared; python setup.py sdist) && pip install --no-cache /collabovid-shared/dist/collabovid-shared-0.1.tar.gz && rm -rf /collabovid-shared

COPY ${PROJECT_DIR} /app
WORKDIR /app
ENV DJANGO_SETTINGS_MODULE=${PROJECT_NAME}.test_settings
RUN python manage.py collectstatic

EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["./run_server.sh"]