FROM python:3.7-slim-buster

RUN apt-get update && apt-get -y --no-install-recommends install cron && rm -rf /var/lib/apt/lists/*

COPY ./sync-daemon/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

COPY sync-daemon/src /app

# Copy executable file to the cron.d directory
RUN mv /app/cronjob /etc/cron.d/cronjob \
# Give execution rights on the cron job
&& chmod 0644 /etc/cron.d/cronjob \
# add to crontab
&& crontab /etc/cron.d/cronjob

CMD ["bash", "/app/start.sh"]