FROM python:3.7-slim-buster

COPY ./docker/shared_requirements.txt /shared_requirements.txt
RUN pip install --no-cache -r /shared_requirements.txt && rm /shared_requirements.txt