from django.shortcuts import render
from data.models import Paper, Topic
import json
import os
from random import randint


# Create your views here.


def classify_index(request):
    file_name = 'classification.json'

    paper_map = {}
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            paper_map = json.load(f)

    if request.method == 'POST':
        chosen_topic_id = request.POST.get('topic')
        paper_id = request.POST.get('paper')
        paper_map[paper_id] = int(chosen_topic_id)
        with open(file_name, 'w+') as f:
            json.dump(paper_map, f)

    done = len(paper_map)
    paper_query = Paper.objects.exclude(pk__in=(paper_map.keys()))
    left = paper_query.count()
    paper = None
    if left > 0:
        #idx = randint(0, left - 1)
        paper = paper_query[0]
    topics = Topic.objects.all()
    return render(request, "classification/index.html", {'paper': paper, 'topics': topics, 'done': done, 'total': left + done})
