FROM collabovid-base:latest

RUN apt-get -y update && apt-get install -y --no-install-recommends nginx \
&& rm -rf /var/lib/apt/lists/*

ENV PROJECT_DIR=web
ENV PROJECT_NAME=web

COPY ./${PROJECT_DIR}/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

COPY collabovid-shared/dist /collabovid-shared/dist
RUN pip install --no-cache /collabovid-shared/dist/*.whl && rm -rf /collabovid-shared

COPY ./collabovid-store/dist /collabovid-store
RUN pip install --no-cache /collabovid-store/*.whl && rm -rf /collabovid-store

COPY ./docker/nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log

COPY ${PROJECT_DIR} /app
WORKDIR /app
ENV DJANGO_SETTINGS_MODULE=${PROJECT_NAME}.settings_prod
ENV SECRET_KEY='xyz'
ENV SECRET_KEY=''

RUN mkdir /cache

EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["./run_server.sh"]