import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')
import django

django.setup()
from data.models import Topic, Paper
import argparse
from tqdm import tqdm
import urllib.request
import json

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-f', '--file')
group.add_argument('-u', '--url')
args = parser.parse_args()

if args.file:
    print(f'Opening file: {args.file}')
    with open(args.file, 'r') as f:
        topics = json.load(f)
elif args.url:
    print(f'Loading from url: {args.url}')
    with urllib.request.urlopen(args.url) as url:
        topics = json.loads(url.read().decode())

paper_topic_dict = {}

print(f'Creating {len(topics)} topics')
for topic in tqdm(topics):
    new_topic = Topic()
    new_topic.name = topic['name']
    new_topic.keywords = topic['keywords']
    new_topic.save()
    for doi in topic['papers']:
        paper_topic_dict[doi] = new_topic

print('Assigning Papers to topics')
for paper in tqdm(list(Paper.objects.all())):
    if paper.doi in paper_topic_dict:
        paper.topic = paper_topic_dict[paper.doi]
    paper.save()

print('Done')
