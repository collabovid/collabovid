FROM python:3.7-slim-buster

COPY ./sync-daemon/requirements.txt /requirements.txt
RUN pip install --no-cache -r /requirements.txt

COPY ./collabovid-store/dist /collabovid-store
RUN pip install --no-cache /collabovid-store/*.whl

COPY sync-daemon/src /app

CMD ["python", "/app/sync.py"]