FROM collabovid-base:latest

ENV PROJECT_DIR=search
ENV PROJECT_NAME=search

COPY ./${PROJECT_DIR}/requirements.txt /requirements.txt
RUN pip install --no-cache --no-warn-script-location -r /requirements.txt -f https://download.pytorch.org/whl/torch_stable.html

COPY ${PROJECT_DIR} /app
WORKDIR /app
ENV DJANGO_SETTINGS_MODULE=${PROJECT_NAME}.settings_prod
#RUN chown -R www-data:www-data /models
RUN python manage.py collectstatic

EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["./run_server.sh"]