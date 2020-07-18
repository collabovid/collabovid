import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django
django.setup()

from data.models import Category, Paper
import random
import argparse
import json

from data.models import CategoryMembership
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=True)
    parser.add_argument('--clear', action='store_true',)
    parser.add_argument('--threshold', type=float, default=0.5)

    args = parser.parse_args()

    if args.clear:
        CategoryMembership.objects.all().delete()
        print("Cleared current category assignments")

    with open(args.file, 'r') as f:
        category_assignments = json.load(f)\

    skipping = 0

    print("Found", len(category_assignments), "entries")

    finished = 0
    for data in category_assignments:

        try:
            paper = Paper.objects.get(doi=data["doi"])

            paper.categories.clear()

            for category, score in data["result"].items():
                if score > args.threshold:
                    paper.categories.add(Category.objects.get(model_identifier=category),
                                         through_defaults={
                        'score': (score - args.threshold) * 2
                    })

            paper.save(set_manually_modified=False)

        except Paper.DoesNotExist:
            print("Skipping", data["doi"])
            skipping += 1
        else:
            if finished % 500 == 0:
                print("Progress", str(finished) + "/" + str(len(category_assignments)))

            finished += 1

    print("Skipped", skipping)
