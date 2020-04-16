from django.shortcuts import render, get_object_or_404
from data.models import Paper, Topic
import json
import os
from random import randint
from classification.models import Token, Category, Classification, Subcategory

# Create your views here.


def classify_index(request, token_str):

    token = get_object_or_404(Token, token=token_str)

    if request.method == 'POST':
        chosen_category_id = int(request.POST.get('category'))
        paper_id = request.POST.get('paper')

        paper = get_object_or_404(Paper, pk=paper_id)
        category = None
        sub_category = None

        if chosen_category_id != -1:
            category = get_object_or_404(Category, pk=chosen_category_id)

        classification = Classification(token=token, paper=paper, category=category, sub_category=sub_category)
        classification.save()

    classifications_done = Classification.objects.filter(token=token)
    done = classifications_done.count()
    paper_query = Paper.objects.exclude(pk__in=classifications_done.values("paper__pk"))
    left = paper_query.count()
    paper = None
    if left > 0:
        #idx = randint(0, left - 1)
        paper = paper_query[0]
    categories = Category.objects.all()
    return render(request, "classification/index.html", {'token':token, 'paper': paper, 'categories': categories, 'done': done, 'total': left + done})
