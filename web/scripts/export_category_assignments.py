import json
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')
import django

django.setup()

from data.models import CategoryMembership, Paper

EXPORT_FILE = 'assignments_25072020.json'
if __name__ == '__main__':
    memberships = []
    for paper in Paper.objects.all():
        scores = {mem.category.model_identifier: mem.score for mem in CategoryMembership.objects.filter(paper=paper)}
        memberships.append({"doi": paper.doi, "result": scores})
    with open(EXPORT_FILE, mode='w') as file:
        json.dump(memberships, file, indent=3)