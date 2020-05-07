FROM python:3.7-slim-buster

RUN apt-get update && apt-get -y --no-install-recommends install cron && rm -rf /var/lib/apt/lists/*

COPY ./sync-deamon/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

COPY sync-deamon/src /app

#Copy hello-cron file to the cron.d directory
RUN mv /app/cronjob /etc/cron.d/cronjob \
# Give execution rights on the cron job
&& chmod 0644 /etc/cron.d/cronjob \
# add to crontab
&& crontab /etc/cron.d/cronjob

CMD ["bash", "/app/start.sh"]